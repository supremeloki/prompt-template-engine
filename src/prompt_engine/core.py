from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


class PromptEngineError(Exception):
    pass


class MissingVariableError(PromptEngineError):
    def __init__(self, variables: Sequence[str]) -> None:
        super().__init__(f"missing template variables: {', '.join(sorted(variables))}")


class UnknownVariableError(PromptEngineError):
    def __init__(self, variables: Sequence[str]) -> None:
        super().__init__(f"unknown template variables: {', '.join(sorted(variables))}")


class TemplateNotFoundError(PromptEngineError):
    pass


VARIABLE_PATTERN: re.Pattern[str] = re.compile(r"\{\{\s*(\w+)\s*\}\}")
CONDITIONAL_PATTERN: re.Pattern[str] = re.compile(
    r"\{% if (\w+) %}(.*?)\{% endif %}", re.DOTALL
)
LOOP_PATTERN: re.Pattern[str] = re.compile(
    r"\{% for (\w+) in (\w+) %}(.*?)\{% endfor %}", re.DOTALL
)


@dataclass(frozen=True)
class RenderResult:
    template_name: str
    prompt: str
    variables_used: tuple[str, ...]
    token_estimate: int


def extract_variables(template: str) -> set[str]:
    return set(VARIABLE_PATTERN.findall(template))


class PromptTemplate:
    def __init__(self, name: str, body: str,
                 validators: dict[str, Callable[[Any], bool]] | None = None) -> None:
        self.name = name
        self.body = body
        self.validators = validators or {}

    @property
    def required_variables(self) -> set[str]:
        stripped = LOOP_PATTERN.sub(" ", self.body)
        stripped = CONDITIONAL_PATTERN.sub(" ", stripped)
        return extract_variables(stripped)

    @property
    def accepted_variables(self) -> set[str]:
        accepted = extract_variables(self.body)
        for match in CONDITIONAL_PATTERN.finditer(self.body):
            accepted.add(match.group(1))
        for match in LOOP_PATTERN.finditer(self.body):
            accepted.add(match.group(1))
            accepted.add(match.group(2))
        return accepted

    def validate(self, context: dict[str, Any]) -> list[str]:
        failures: list[str] = []
        for variable, validator in self.validators.items():
            if variable in context and not validator(context[variable]):
                failures.append(variable)
        return failures

    def render(self, context: dict[str, Any] | None = None) -> str:
        context = context or {}
        missing = self.required_variables - set(context)
        if missing:
            raise MissingVariableError(missing)
        unknown = set(context) - self.accepted_variables
        if unknown:
            raise UnknownVariableError(unknown)
        failed = self.validate(context)
        if failed:
            raise PromptEngineError(f"validation failed for: {', '.join(failed)}")
        return expand_loops(self.body, expand_conditionals(self.body, context), context)

    def render_with_report(self, context: dict[str, Any] | None = None) -> RenderResult:
        prompt = self.render(context)
        return RenderResult(
            template_name=self.name,
            prompt=prompt,
            variables_used=tuple(sorted((context or {}).keys())),
            token_estimate=len(prompt.split()),
        )


def _resolve_sections(body: str, context: dict[str, Any],
                      keep: Callable[[str], bool]) -> str:
    def replace(match: re.Match[str]) -> str:
        return match.group(2) if keep(match.group(1)) else ""

    result = ""
    position = 0
    for match in CONDITIONAL_PATTERN.finditer(body):
        result += body[position:match.start()]
        result += match.group(2) if keep(match.group(1)) else ""
        position = match.end()
    result += body[position:]
    del replace
    return result


def expand_conditionals(body: str, context: dict[str, Any]) -> str:
    def keep(name: str) -> bool:
        return bool(context.get(name))

    return _resolve_sections(body, context, keep)


def expand_loops(original: str, expanded_conditionals: str,
                 context: dict[str, Any]) -> str:
    source = original if LOOP_PATTERN.search(original) else expanded_conditionals

    def render_loop(match: re.Match[str]) -> str:
        item_name, list_name, inner = match.group(1), match.group(2), match.group(3)
        items = context.get(list_name, [])
        rendered_parts: list[str] = []
        for item in items:
            scoped = dict(context)
            scoped[item_name] = item
            section = VARIABLE_PATTERN.sub(
                lambda m: str(scoped.get(m.group(1), "")), inner
            )
            section = CONDITIONAL_PATTERN.sub(
                lambda m: m.group(2) if scoped.get(m.group(1)) else "", section
            )
            rendered_parts.append(section.strip())
        return "\n".join(rendered_parts)

    output = LOOP_PATTERN.sub(render_loop, source)
    output = CONDITIONAL_PATTERN.sub(
        lambda m: m.group(2) if context.get(m.group(1)) else "", output
    )
    return VARIABLE_PATTERN.sub(lambda m: str(context.get(m.group(1), "")), output).strip()


class TemplateLibrary:
    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> "TemplateLibrary":
        self._templates[template.name] = template
        return self

    def load_directory(self, directory: Path) -> "TemplateLibrary":
        for path in sorted(directory.glob("*.md")) + sorted(directory.glob("*.txt")):
            name = path.stem
            self._templates[name] = PromptTemplate(name, path.read_text(encoding="utf-8"))
        return self

    def get(self, name: str) -> PromptTemplate:
        template = self._templates.get(name)
        if template is None:
            raise TemplateNotFoundError(f"template {name!r} not registered")
        return template

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._templates))


DEFAULT_SYSTEM_TEMPLATE = PromptTemplate(
    name="default-system",
    body=(
        "You are {{role}}.\n"
        "{% if tone %}Respond with a {{tone}} tone.{% endif %}\n"
        "Task: {{task}}"
    ),
)

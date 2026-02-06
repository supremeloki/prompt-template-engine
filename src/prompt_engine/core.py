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


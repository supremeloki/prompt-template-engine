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


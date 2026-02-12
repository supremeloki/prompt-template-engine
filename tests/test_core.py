import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from prompt_engine import (
    DEFAULT_SYSTEM_TEMPLATE,
    MissingVariableError,
    PromptEngineError,
    PromptTemplate,
    TemplateLibrary,
    TemplateNotFoundError,
    UnknownVariableError,
    extract_variables,
)


def test_extract_variables_finds_all():
    found = extract_variables("Hello {{name}}, you are {{ role }} today")
    assert found == {"name", "role"}


def test_basic_render():
    template = PromptTemplate("greet", "Hello {{name}}!")
    assert template.render({"name": "Koor"}) == "Hello Koor!"


def test_missing_variable_raises():
    template = PromptTemplate("greet", "Hello {{name}} from {{city}}")
    with pytest.raises(MissingVariableError):
        template.render({"name": "Koor"})


def test_unknown_variable_rejected():
    template = PromptTemplate("strict", "Hi {{name}}")
    with pytest.raises(UnknownVariableError):
        template.render({"name": "x", "extra": "y"})


def test_conditional_included_when_truthy():
    template = PromptTemplate("t", "{% if formal %}Dear Sir,{% endif %} {{body}}")
    assert "Dear Sir" in template.render({"formal": True, "body": "hi"})
    assert "Dear Sir" not in template.render({"formal": False, "body": "hi"})


def test_loop_expands_per_item():
    body = "{% for item in items %}- {{item}}{% endfor %}"
    template = PromptTemplate("list", body)
    rendered = template.render({"items": ["a", "b", "c"]})
    assert "- a" in rendered and "- b" in rendered and "- c" in rendered


def test_validator_blocks_bad_value():
    template = PromptTemplate(
        "validated", "Age is {{age}}",
        validators={"age": lambda v: isinstance(v, int) and v > 0},
    )
    with pytest.raises(PromptEngineError):
        template.render({"age": -3})
    assert "33" in template.render({"age": 33})


def test_render_report_counts_tokens():

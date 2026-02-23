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
    template = PromptTemplate("report", "one two three {{x}}")
    result = template.render_with_report({"x": "four"})
    assert result.token_estimate == 4
    assert result.variables_used == ("x",)
    assert result.template_name == "report"


def test_library_register_and_get():
    library = TemplateLibrary()
    library.register(PromptTemplate("summarize", "Summarize: {{text}}"))
    assert library.get("summarize").render({"text": "stuff"}) == "Summarize: stuff"


def test_library_missing_template_raises():
    with pytest.raises(TemplateNotFoundError):
        TemplateLibrary().get("ghost")


def test_library_loads_from_directory(tmp_path):
    (tmp_path / "translate.md").write_text("Translate to {{lang}}: {{text}}",
                                           encoding="utf-8")
    library = TemplateLibrary().load_directory(tmp_path)
    assert "translate" in library.names
    rendered = library.get("translate").render({"lang": "de", "text": "hello"})
    assert "de" in rendered


def test_default_system_template_renders():
    prompt = DEFAULT_SYSTEM_TEMPLATE.render({
        "role": "a code reviewer", "task": "review this diff",
    })
    assert "code reviewer" in prompt
    assert "review this diff" in prompt


def test_conditional_absent_by_default_in_default_template():
    prompt = DEFAULT_SYSTEM_TEMPLATE.render({
        "role": "assistant", "task": "help",
    })
    assert "tone" not in prompt



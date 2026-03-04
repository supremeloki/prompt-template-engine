# prompt-engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A strict prompt template engine for LLM apps: `{{variables}}`, `{% if %}` conditionals, `{% for %}` loops, per-variable validators, and a template library that loads straight from markdown files.

## 🚀 Overview

String formatting hides prompt bugs until runtime. `prompt-engine` fails loudly and early: missing variables raise `MissingVariableError`, unexpected context keys raise `UnknownVariableError` (catches typos like `{{user_name}}` vs `username`), and validators block invalid values before they reach the model. Conditionals and loops cover the structural cases — optional sections and list rendering — without pulling in Jinja.

## ✨ Features

- **Strict variable contract:** missing → error, unknown → error, typos can't slip through
- **Validators:** per-variable predicates (`age > 0`) enforced at render time
- **Conditionals:** `{% if flag %}...{% endif %}` — flags are accepted context keys, not required
- **Loops:** `{% for item in items %}...{% endfor %}` with scoped variable resolution
- **TemplateLibrary:** register programmatically or bulk-load `*.md`/`*.txt` from a directory
- **RenderResult:** rendered prompt + variables used + token estimate
- **Zero dependencies**

## 🚧 Structure

```
prompt-template-engine/
├── src/prompt_engine/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/prompt-template-engine.git
cd prompt-template-engine
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from prompt_engine import PromptTemplate, TemplateLibrary

template = PromptTemplate(
    "review",
    "Review this {{language}} code:\n{{code}}\n"
    "{% if strict %}Be strict about style.{% endif %}",
    validators={"code": lambda c: len(c) < 10_000},
)

print(template.render({"language": "Python", "code": "x=1", "strict": True}))

library = TemplateLibrary().load_directory(Path("prompts"))
print(library.names)
```

## 🔧 Error Handling

```text
PromptEngineError
├── MissingVariableError    # required {{var}} absent from context
├── UnknownVariableError    # context key no slot accepts (typo guard)
├── TemplateNotFoundError   # library lookup miss
└── validation failure      # a validator predicate returned False
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen render results
- Zero comments — names carry the meaning
- Strict-contract behavior (missing/unknown/validation) fully covered

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi** - [kooroushmasoumi@gmail.com](mailto:kooroushmasoumi@gmail.com)

---

⭐ Star this repo if you find it useful!

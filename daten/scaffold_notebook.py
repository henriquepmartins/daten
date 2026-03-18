from __future__ import annotations

from pathlib import Path

from daten.bootstrap import (
    InitConfig,
    append_block_if_missing,
    copy_env_example_if_missing,
    populate_empty_directories,
    write_file,
)
from daten.uv_runner import UVRunner

NOTEBOOK_RUNTIME_DEPS = [
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "scikit-learn",
    "xgboost",
    "lightgbm",
    "jupyterlab",
    "ipykernel",
    "python-dotenv",
]

NOTEBOOK_DEV_DEPS = [
    "ruff",
    "pytest",
    "pytest-cov",
    "pre-commit",
]


def scaffold(config: InitConfig, runner: UVRunner) -> None:
    runner.init_project(config.project_root, config.slug, config.python_version, config.git)
    _create_structure(config.project_root, config.slug)
    _write_files(config.project_root, config.slug, config.project_name)
    runner.add(NOTEBOOK_RUNTIME_DEPS, cwd=config.project_root)
    runner.add(NOTEBOOK_DEV_DEPS, cwd=config.project_root, group="dev")
    _append_pyproject_tooling(config.project_root)
    runner.sync(cwd=config.project_root)
    if config.export_requirements:
        runner.export_requirements(config.project_root, "requirements.txt")
        runner.export_requirements(config.project_root, "requirements-dev.txt", only_dev=True)


def _create_structure(project_root: Path, slug: str) -> None:
    populate_empty_directories(
        [
            project_root / "notebooks",
            project_root / "data" / "raw",
            project_root / "data" / "interim",
            project_root / "data" / "processed",
            project_root / "data" / "external",
            project_root / "models",
            project_root / "reports" / "figures",
            project_root / "tests",
        ]
    )
    (project_root / "src" / slug).mkdir(parents=True, exist_ok=True)


def _write_files(project_root: Path, slug: str, project_name: str) -> None:
    write_file(project_root / "src" / slug / "__init__.py", notebook_init_file())
    write_file(project_root / "src" / slug / "paths.py", notebook_paths_file())
    write_file(project_root / "tests" / "test_smoke.py", notebook_test_file(slug))
    write_file(project_root / ".env.example", notebook_env_example())
    copy_env_example_if_missing(project_root)
    write_file(project_root / ".gitignore", notebook_gitignore())
    write_file(project_root / "Makefile", notebook_makefile(slug))
    write_file(project_root / "README.md", notebook_readme(project_name, slug))
    write_file(project_root / "notebooks" / "01_exploration.ipynb", notebook_placeholder(project_name, slug))


def _append_pyproject_tooling(project_root: Path) -> None:
    append_block_if_missing(project_root / "pyproject.toml", NOTEBOOK_TOOLING)


def notebook_init_file() -> str:
    return '''def main() -> None:
    print("Notebook project ready. Run `uv run jupyter lab` to start exploring.")
'''


def notebook_paths_file() -> str:
    return '''from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"
'''


def notebook_test_file(slug: str) -> str:
    return f'''from {slug} import main


def test_main_runs(capsys) -> None:
    main()
    captured = capsys.readouterr()
    assert "Notebook project ready" in captured.out
'''


def notebook_env_example() -> str:
    return """DATA_DIR=data
MODELS_DIR=models
RANDOM_SEED=42
LOG_LEVEL=INFO
"""


def notebook_gitignore() -> str:
    return """.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.ipynb_checkpoints/
.DS_Store
.env
data/raw/*
data/interim/*
data/processed/*
data/external/*
models/*
!data/raw/.gitkeep
!data/interim/.gitkeep
!data/processed/.gitkeep
!data/external/.gitkeep
!models/.gitkeep
"""


def notebook_makefile(slug: str) -> str:
    return f"""sync:
\tuv sync

lint:
\tuv run ruff check .

test:
\tuv run pytest

notebook:
\tuv run jupyter lab

export:
\tuv export --format requirements.txt --output-file requirements.txt --no-dev --no-emit-project
\tuv export --format requirements.txt --output-file requirements-dev.txt --only-dev --no-emit-project

package-info:
\tuv run python -c "import {slug}; print({slug}.__name__)"
"""


def notebook_readme(project_name: str, slug: str) -> str:
    return f"""# {project_name}

Project scaffold for exploratory data science and lightweight ML training.

## Quickstart

```bash
uv sync
uv run jupyter lab
```

## Layout

- `src/{slug}`: reusable project code.
- `notebooks/`: exploratory notebooks.
- `data/`: raw, interim, processed and external datasets.
- `models/`: saved artifacts.
- `reports/figures/`: charts and exports.

## Common commands

```bash
make notebook
make test
make lint
```
"""


def notebook_placeholder(project_name: str, slug: str) -> str:
    return f'''{{
 "cells": [
  {{
   "cell_type": "markdown",
   "metadata": {{}},
   "source": [
    "# {project_name}\\n",
    "Notebook inicial para EDA, testes de features e treinos rapidos."
   ]
  }},
  {{
   "cell_type": "code",
   "execution_count": null,
   "metadata": {{}},
   "outputs": [],
   "source": [
    "import pandas as pd\\n",
    "from {slug}.paths import DATA_DIR\\n",
    "\\n",
    "print(DATA_DIR)"
   ]
  }}
 ],
 "metadata": {{
  "kernelspec": {{
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }},
  "language_info": {{
   "name": "python",
   "version": "3.12"
  }}
 }},
 "nbformat": 4,
 "nbformat_minor": 5
}}
'''


NOTEBOOK_TOOLING = """
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[tool.pytest.ini_options]
pythonpath = ["src"]
addopts = "-q"
testpaths = ["tests"]
"""

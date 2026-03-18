from pathlib import Path

from typer.testing import CliRunner

import daten.cli as cli_module
from daten.bootstrap import DeployTarget, TemplateType
from daten.cli import app
from tests.test_scaffolds import RecordingUVRunner

runner = CliRunner()


def test_version_flag_returns_current_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_init_generates_notebook_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli_module.bootstrap, "ensure_uv_available", lambda: "/fake/uv")
    monkeypatch.setattr(cli_module.bootstrap, "ensure_git_available", lambda require_git: None)
    monkeypatch.setattr(cli_module, "UVRunner", lambda *_args, **_kwargs: RecordingUVRunner())

    result = runner.invoke(
        app,
        [
            "init",
            "eda-project",
            "--template",
            TemplateType.NOTEBOOK.value,
            "--path",
            str(tmp_path),
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "eda-project" / "notebooks" / "01_exploration.ipynb").exists()


def test_init_generates_production_serverless_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli_module.bootstrap, "ensure_uv_available", lambda: "/fake/uv")
    monkeypatch.setattr(cli_module.bootstrap, "ensure_git_available", lambda require_git: None)
    monkeypatch.setattr(cli_module, "UVRunner", lambda *_args, **_kwargs: RecordingUVRunner())

    result = runner.invoke(
        app,
        [
            "init",
            "scoring-api",
            "--template",
            TemplateType.PRODUCTION.value,
            "--deploy-target",
            DeployTarget.SERVERLESS.value,
            "--path",
            str(tmp_path),
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "scoring-api" / "src" / "scoring_api" / "handler.py").exists()


def test_init_fails_for_non_empty_directory(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "existing-project"
    project_root.mkdir()
    (project_root / "README.md").write_text("occupied", encoding="utf-8")

    monkeypatch.setattr(cli_module.bootstrap, "ensure_uv_available", lambda: "/fake/uv")
    monkeypatch.setattr(cli_module.bootstrap, "ensure_git_available", lambda require_git: None)
    monkeypatch.setattr(cli_module, "UVRunner", lambda *_args, **_kwargs: RecordingUVRunner())

    result = runner.invoke(
        app,
        [
            "init",
            "existing-project",
            "--template",
            TemplateType.NOTEBOOK.value,
            "--path",
            str(tmp_path),
            "--yes",
        ],
    )

    assert result.exit_code == 1
    assert "not empty" in result.stderr

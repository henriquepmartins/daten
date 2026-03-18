from pathlib import Path

import pytest

from daten.bootstrap import (
    BootstrapError,
    brew_install_command,
    copy_env_example_if_missing,
    ensure_target_directory,
    official_uv_install_command,
    slugify_project_name,
)


def test_slugify_project_name_normalizes_input() -> None:
    assert slugify_project_name("Meu Projeto 123") == "meu_projeto_123"
    assert slugify_project_name("123 app") == "project_123_app"
    assert slugify_project_name("!!!") == "project"


def test_copy_env_example_if_missing_creates_env_file(tmp_path: Path) -> None:
    project_root = tmp_path / "demo"
    project_root.mkdir()
    (project_root / ".env.example").write_text("LOG_LEVEL=INFO\n", encoding="utf-8")

    copy_env_example_if_missing(project_root)

    assert (project_root / ".env").read_text(encoding="utf-8") == "LOG_LEVEL=INFO\n"


def test_copy_env_example_if_missing_does_not_override_existing_env(tmp_path: Path) -> None:
    project_root = tmp_path / "demo"
    project_root.mkdir()
    (project_root / ".env.example").write_text("LOG_LEVEL=INFO\n", encoding="utf-8")
    (project_root / ".env").write_text("LOG_LEVEL=DEBUG\n", encoding="utf-8")

    copy_env_example_if_missing(project_root)

    assert (project_root / ".env").read_text(encoding="utf-8") == "LOG_LEVEL=DEBUG\n"


def test_ensure_target_directory_rejects_non_empty_directories(tmp_path: Path) -> None:
    project_root = tmp_path / "demo"
    project_root.mkdir()
    (project_root / "file.txt").write_text("content", encoding="utf-8")

    with pytest.raises(BootstrapError):
        ensure_target_directory(project_root)


def test_brew_and_official_install_commands_are_expected() -> None:
    assert brew_install_command("uv") == ["brew", "install", "uv"]
    assert official_uv_install_command() == ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]

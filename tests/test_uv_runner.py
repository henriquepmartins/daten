from pathlib import Path

from daten.uv_runner import UVRunner


def test_build_add_command_supports_groups() -> None:
    runner = UVRunner("/custom/uv")

    assert runner.build_add_command(["fastapi", "uvicorn"], group="dev") == [
        "/custom/uv",
        "add",
        "--no-sync",
        "--group",
        "dev",
        "fastapi",
        "uvicorn",
    ]


def test_build_export_command_matches_expected_shape() -> None:
    runner = UVRunner()

    assert runner.build_export_command("requirements.txt") == [
        "uv",
        "export",
        "--format",
        "requirements.txt",
        "--output-file",
        "requirements.txt",
        "--no-emit-project",
        "--no-dev",
    ]
    assert runner.build_export_command("requirements-dev.txt", only_dev=True)[-1] == "--only-dev"


def test_build_init_command_uses_target_path_and_git() -> None:
    runner = UVRunner()
    command = runner.build_init_command(Path("/tmp/demo"), "demo_pkg", "3.12", git=True)

    assert command == [
        "uv",
        "init",
        "--package",
        "--python",
        "3.12",
        "--vcs",
        "git",
        "--name",
        "demo_pkg",
        "/tmp/demo",
    ]

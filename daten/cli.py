from __future__ import annotations

from pathlib import Path

import typer

from daten import __version__
from daten import bootstrap
from daten.bootstrap import BootstrapError, DeployTarget, TemplateType
from daten.doctor import collect_checks, is_healthy
from daten.prompts import PromptAbortedError, resolve_init_config
from daten.scaffold_notebook import scaffold as scaffold_notebook
from daten.scaffold_production import scaffold as scaffold_production
from daten.uv_runner import UVCommandError, UVRunner

app = typer.Typer(
    no_args_is_help=True,
    invoke_without_command=True,
    help="Scaffold data science and ML projects with uv.",
)


def print_error(message: str) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)


def print_success(message: str) -> None:
    typer.secho(message, fg=typer.colors.GREEN)


@app.command()
def doctor() -> None:
    """Inspect the local environment used by daten."""

    checks = collect_checks()
    for check in checks:
        label = {"ok": "[ok]", "warning": "[warn]", "error": "[error]"}[check.status]
        color = {
            "ok": typer.colors.GREEN,
            "warning": typer.colors.YELLOW,
            "error": typer.colors.RED,
        }[check.status]
        typer.secho(f"{label} {check.name}: {check.detail}", fg=color)

    if not is_healthy(checks):
        raise typer.Exit(code=1)


@app.command("init")
def init_command(
    project_name: str = typer.Argument(..., help="Directory name for the generated project."),
    template: TemplateType | None = typer.Option(None, help="Project template."),
    path: Path = typer.Option(Path.cwd(), help="Parent directory where the project will be created."),
    python: str = typer.Option("3.12", help="Python version pinned in the generated project."),
    git: bool = typer.Option(True, "--git/--no-git", help="Initialize the generated project with git."),
    export_requirements: bool = typer.Option(
        True,
        "--export-requirements/--no-export-requirements",
        help="Export requirements.txt and requirements-dev.txt from uv.lock.",
    ),
    deploy_target: DeployTarget | None = typer.Option(None, help="Deploy target for production projects."),
    yes: bool = typer.Option(False, "--yes", help="Run non-interactively using defaults."),
) -> None:
    """Create a new project from one of the available templates."""

    try:
        config = resolve_init_config(
            project_name=project_name,
            base_path=path,
            template=template,
            python_version=python,
            git=git,
            export_requirements=export_requirements,
            deploy_target=deploy_target,
            yes=yes,
        )
        bootstrap.ensure_target_directory(config.project_root)
        bootstrap.ensure_git_available(config.git)
        uv_path = bootstrap.ensure_uv_available()
        runner = UVRunner(uv_path)
        runner.python_install(config.python_version)

        if config.template == TemplateType.NOTEBOOK:
            scaffold_notebook(config, runner)
        else:
            scaffold_production(config, runner)

        print_success(f"Project created at {config.project_root}")
    except PromptAbortedError as exc:
        print_error(str(exc))
        raise typer.Exit(code=1) from exc
    except (BootstrapError, UVCommandError) as exc:
        print_error(str(exc))
        raise typer.Exit(code=1) from exc


@app.callback()
def main_callback(version: bool = typer.Option(False, "--version", help="Show the CLI version.")) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


def main() -> None:
    app()

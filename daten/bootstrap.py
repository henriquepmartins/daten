from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class TemplateType(str, Enum):
    NOTEBOOK = "notebook"
    PRODUCTION = "production"


class DeployTarget(str, Enum):
    CONTAINER = "container"
    SERVERLESS = "serverless"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class InitConfig:
    project_name: str
    slug: str
    project_root: Path
    template: TemplateType
    python_version: str = "3.12"
    git: bool = True
    export_requirements: bool = True
    deploy_target: DeployTarget | None = None


@dataclass(frozen=True)
class PlatformInfo:
    system: str
    brew_path: str | None
    uv_path: str | None
    python_path: str | None
    git_path: str | None
    docker_path: str | None

    @property
    def is_macos(self) -> bool:
        return self.system == "Darwin"


class BootstrapError(RuntimeError):
    pass


def detect_platform() -> PlatformInfo:
    return PlatformInfo(
        system=platform.system(),
        brew_path=shutil.which("brew"),
        uv_path=shutil.which("uv"),
        python_path=shutil.which("python3"),
        git_path=shutil.which("git"),
        docker_path=shutil.which("docker"),
    )


def slugify_project_name(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    if not slug:
        return "project"
    if slug[0].isdigit():
        return f"project_{slug}"
    return slug


def resolve_project_root(base_path: Path | str, project_name: str) -> Path:
    return Path(base_path).expanduser().resolve() / project_name


def ensure_target_directory(project_root: Path) -> None:
    if project_root.exists() and any(project_root.iterdir()):
        raise BootstrapError(f"Target directory already exists and is not empty: {project_root}")
    project_root.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        write_file(path, content)


def append_block_if_missing(path: Path, block: str) -> None:
    existing = path.read_text(encoding="utf-8")
    cleaned = block.strip()
    if cleaned in existing:
        return
    path.write_text(f"{existing.rstrip()}\n\n{cleaned}\n", encoding="utf-8")


def populate_empty_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        marker = path / ".gitkeep"
        if not marker.exists():
            marker.write_text("", encoding="utf-8")


def copy_env_example_if_missing(project_root: Path) -> None:
    env_path = project_root / ".env"
    example_path = project_root / ".env.example"
    if not env_path.exists() and example_path.exists():
        env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")


def brew_install_command(package: str) -> list[str]:
    return ["brew", "install", package]


def official_uv_install_command() -> list[str]:
    return ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]


def run_system_command(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def ensure_uv_available() -> str:
    info = detect_platform()
    if info.uv_path:
        return info.uv_path

    if info.is_macos:
        if not info.brew_path:
            raise BootstrapError(
                "Homebrew is required on macOS to install uv automatically. Install Homebrew first."
            )
        try:
            run_system_command(brew_install_command("uv"))
        except subprocess.CalledProcessError as exc:
            raise BootstrapError(
                "Failed to install uv with Homebrew. Install uv manually and retry."
            ) from exc
    else:
        try:
            run_system_command(official_uv_install_command())
        except subprocess.CalledProcessError as exc:
            raise BootstrapError("Failed to install uv with the official installer.") from exc

    uv_path = shutil.which("uv")
    if not uv_path:
        raise BootstrapError("uv is still unavailable after the installation attempt.")
    return uv_path


def ensure_git_available(require_git: bool) -> None:
    if require_git and shutil.which("git") is None:
        raise BootstrapError("Git is required for --git. Install git or rerun with --no-git.")

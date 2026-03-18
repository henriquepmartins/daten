from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence


class UVCommandError(RuntimeError):
    pass


class UVRunner:
    def __init__(self, executable: str = "uv") -> None:
        self.executable = executable

    def build_python_install_command(self, python_version: str) -> list[str]:
        return [self.executable, "python", "install", python_version]

    def build_init_command(
        self,
        project_root: Path,
        slug: str,
        python_version: str,
        git: bool,
    ) -> list[str]:
        return [
            self.executable,
            "init",
            "--package",
            "--python",
            python_version,
            "--vcs",
            "git" if git else "none",
            "--name",
            slug,
            str(project_root),
        ]

    def build_add_command(self, dependencies: Sequence[str], group: str | None = None) -> list[str]:
        command = [self.executable, "add", "--no-sync"]
        if group:
            command.extend(["--group", group])
        command.extend(dependencies)
        return command

    def build_sync_command(self) -> list[str]:
        return [self.executable, "sync"]

    def build_export_command(self, output_file: str, only_dev: bool = False) -> list[str]:
        command = [
            self.executable,
            "export",
            "--format",
            "requirements.txt",
            "--output-file",
            output_file,
            "--no-emit-project",
        ]
        command.append("--only-dev" if only_dev else "--no-dev")
        return command

    def run(self, command: list[str], cwd: Path | None = None) -> None:
        try:
            subprocess.run(command, cwd=cwd, check=True)
        except subprocess.CalledProcessError as exc:
            rendered = " ".join(command)
            raise UVCommandError(f"Command failed: {rendered}") from exc

    def python_install(self, python_version: str) -> None:
        self.run(self.build_python_install_command(python_version))

    def init_project(self, project_root: Path, slug: str, python_version: str, git: bool) -> None:
        self.run(self.build_init_command(project_root, slug, python_version, git))

    def add(self, dependencies: Sequence[str], cwd: Path, group: str | None = None) -> None:
        if dependencies:
            self.run(self.build_add_command(dependencies, group=group), cwd=cwd)

    def sync(self, cwd: Path) -> None:
        self.run(self.build_sync_command(), cwd=cwd)

    def export_requirements(self, cwd: Path, output_file: str, only_dev: bool = False) -> None:
        self.run(self.build_export_command(output_file, only_dev=only_dev), cwd=cwd)

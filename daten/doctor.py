from __future__ import annotations

from dataclasses import dataclass

from daten.bootstrap import PlatformInfo, detect_platform


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def collect_checks() -> list[CheckResult]:
    info = detect_platform()
    results = [CheckResult("platform", "ok", render_platform(info))]

    if info.is_macos:
        results.append(
            CheckResult(
                "homebrew",
                "ok" if info.brew_path else "error",
                info.brew_path or "Homebrew not found on PATH",
            )
        )

    results.extend(
        [
            CheckResult("uv", "ok" if info.uv_path else "error", info.uv_path or "uv not found"),
            CheckResult(
                "python3",
                "ok" if info.python_path else "error",
                info.python_path or "python3 not found",
            ),
            CheckResult("git", "ok" if info.git_path else "warning", info.git_path or "git not found"),
            CheckResult(
                "docker",
                "ok" if info.docker_path else "warning",
                info.docker_path or "docker not found",
            ),
        ]
    )
    return results


def render_platform(info: PlatformInfo) -> str:
    return "macOS" if info.is_macos else info.system


def is_healthy(checks: list[CheckResult]) -> bool:
    return not any(check.status == "error" for check in checks)

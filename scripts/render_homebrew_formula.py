from __future__ import annotations

import hashlib
import tarfile
import tomllib
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
FORMULA_PATH = ROOT / "homebrew-tap" / "Formula" / "daten.rb"
DIST_DIR = ROOT / "dist"
LOCKFILE = ROOT / "uv.lock"
REPO_ARCHIVE_URL = "https://github.com/henriquepmartins/daten/archive/refs/tags/v{version}.tar.gz"


def read_version() -> str:
    for line in PYPROJECT.read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split('"')[1]
    raise RuntimeError("Could not find version in pyproject.toml")


def sdist_path(version: str) -> Path:
    path = DIST_DIR / f"daten-{version}.tar.gz"
    if not path.exists():
        raise FileNotFoundError(f"Build the sdist first: {path} not found")
    return path


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_for_url(url: str) -> str:
    digest = hashlib.sha256()
    with urllib.request.urlopen(url) as response:
        for chunk in iter(lambda: response.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_sdist(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        names = archive.getnames()
    if not any(name.endswith("pyproject.toml") for name in names):
        raise RuntimeError("Invalid sdist: pyproject.toml not found inside archive")


def load_lock_packages() -> dict[str, dict]:
    lock = tomllib.loads(LOCKFILE.read_text(encoding="utf-8"))
    return {pkg["name"]: pkg for pkg in lock["package"]}


def include_dependency(dep: dict) -> bool:
    marker = dep.get("marker")
    if marker and "win32" in marker:
        return False
    return True


def runtime_closure(packages: dict[str, dict]) -> list[dict]:
    root = packages["daten"]
    pending = [dep["name"] for dep in root.get("dependencies", []) if include_dependency(dep)]
    seen: set[str] = set()
    resolved: list[dict] = []

    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.add(name)
        package = packages[name]
        resolved.append(package)
        for dep in package.get("dependencies", []):
            if include_dependency(dep):
                pending.append(dep["name"])

    return sorted(resolved, key=lambda pkg: pkg["name"])


def render_resources(packages: list[dict]) -> str:
    blocks: list[str] = []
    for package in packages:
        sdist = package.get("sdist")
        if not sdist:
            raise RuntimeError(f"Missing sdist metadata for {package['name']}")
        blocks.append(
            f'''  resource "{package["name"]}" do
    url "{sdist["url"]}"
    sha256 "{sdist["hash"].split(":", 1)[1]}"
  end'''
        )
    return "\n\n".join(blocks)


def render_formula(version: str, sha256: str, resources: str) -> str:
    return f'''class Daten < Formula
  include Language::Python::Virtualenv

  desc "Scaffold data science and ML projects with uv"
  homepage "https://github.com/henriquepmartins/daten"
  url "{REPO_ARCHIVE_URL.format(version=version)}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.12"
  depends_on "uv"

{resources}

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/daten --version")
  end
end
'''


def main() -> None:
    version = read_version()
    path = sdist_path(version)
    validate_sdist(path)
    resources = render_resources(runtime_closure(load_lock_packages()))
    formula = render_formula(version, sha256_for_url(REPO_ARCHIVE_URL.format(version=version)), resources)
    FORMULA_PATH.parent.mkdir(parents=True, exist_ok=True)
    FORMULA_PATH.write_text(formula, encoding="utf-8")
    print(FORMULA_PATH)


if __name__ == "__main__":
    main()

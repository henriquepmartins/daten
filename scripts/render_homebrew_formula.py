from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
FORMULA_PATH = ROOT / "homebrew-tap" / "Formula" / "daten.rb"
DIST_DIR = ROOT / "dist"


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


def validate_sdist(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        names = archive.getnames()
    if not any(name.endswith("pyproject.toml") for name in names):
        raise RuntimeError("Invalid sdist: pyproject.toml not found inside archive")


def render_formula(version: str, sha256: str) -> str:
    return f'''class Daten < Formula
  include Language::Python::Virtualenv

  desc "Scaffold data science and ML projects with uv"
  homepage "https://pypi.org/project/daten/"
  url "https://files.pythonhosted.org/packages/source/d/daten/daten-{version}.tar.gz"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.12"
  depends_on "uv"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install_and_link buildpath
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
    formula = render_formula(version, sha256_for(path))
    FORMULA_PATH.parent.mkdir(parents=True, exist_ok=True)
    FORMULA_PATH.write_text(formula, encoding="utf-8")
    print(FORMULA_PATH)


if __name__ == "__main__":
    main()

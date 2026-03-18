from pathlib import Path

from daten.bootstrap import DeployTarget, InitConfig, TemplateType
from daten.scaffold_notebook import scaffold as scaffold_notebook
from daten.scaffold_production import scaffold as scaffold_production


class RecordingUVRunner:
    def __init__(self, *_args, **_kwargs) -> None:
        self.calls: list[tuple[str, object]] = []

    def python_install(self, python_version: str) -> None:
        self.calls.append(("python_install", python_version))

    def init_project(self, project_root: Path, slug: str, python_version: str, git: bool) -> None:
        self.calls.append(("init_project", project_root, slug, python_version, git))
        package_dir = project_root / "src" / slug
        package_dir.mkdir(parents=True, exist_ok=True)
        (project_root / "pyproject.toml").write_text(
            "[project]\nname = 'demo'\nversion = '0.1.0'\ndependencies = []\n",
            encoding="utf-8",
        )
        (project_root / "README.md").write_text("", encoding="utf-8")
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (project_root / ".python-version").write_text(python_version, encoding="utf-8")

    def add(self, dependencies: list[str], cwd: Path, group: str | None = None) -> None:
        self.calls.append(("add", tuple(dependencies), cwd, group))

    def sync(self, cwd: Path) -> None:
        self.calls.append(("sync", cwd))
        (cwd / "uv.lock").write_text("", encoding="utf-8")
        (cwd / ".venv").mkdir(exist_ok=True)

    def export_requirements(self, cwd: Path, output_file: str, only_dev: bool = False) -> None:
        self.calls.append(("export", cwd, output_file, only_dev))
        (cwd / output_file).write_text("# generated\n", encoding="utf-8")


def test_notebook_scaffold_creates_expected_structure(tmp_path: Path) -> None:
    runner = RecordingUVRunner()
    config = InitConfig(
        project_name="credit-notebook",
        slug="credit_notebook",
        project_root=tmp_path / "credit-notebook",
        template=TemplateType.NOTEBOOK,
    )

    scaffold_notebook(config, runner)

    assert (config.project_root / "notebooks" / "01_exploration.ipynb").exists()
    assert (config.project_root / ".env").exists()
    assert (config.project_root / "requirements.txt").exists()
    assert (config.project_root / "src" / config.slug / "paths.py").exists()


def test_production_scaffold_writes_container_artifacts(tmp_path: Path) -> None:
    runner = RecordingUVRunner()
    config = InitConfig(
        project_name="fraud-api",
        slug="fraud_api",
        project_root=tmp_path / "fraud-api",
        template=TemplateType.PRODUCTION,
        deploy_target=DeployTarget.CONTAINER,
    )

    scaffold_production(config, runner)

    assert (config.project_root / "Dockerfile").exists()
    assert (config.project_root / "compose.yaml").exists()
    assert (config.project_root / "src" / config.slug / "main.py").exists()
    assert (config.project_root / "requirements-dev.txt").exists()


def test_production_scaffold_writes_serverless_handler(tmp_path: Path) -> None:
    runner = RecordingUVRunner()
    config = InitConfig(
        project_name="fraud-api",
        slug="fraud_api",
        project_root=tmp_path / "fraud-serverless",
        template=TemplateType.PRODUCTION,
        deploy_target=DeployTarget.SERVERLESS,
    )

    scaffold_production(config, runner)

    assert (config.project_root / "src" / config.slug / "handler.py").exists()
    assert not (config.project_root / "Dockerfile").exists()

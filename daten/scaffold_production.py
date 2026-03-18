from __future__ import annotations

from pathlib import Path

from daten.bootstrap import (
    DeployTarget,
    InitConfig,
    append_block_if_missing,
    copy_env_example_if_missing,
    populate_empty_directories,
    write_file,
)
from daten.uv_runner import UVRunner

PRODUCTION_RUNTIME_DEPS = [
    "fastapi",
    "uvicorn[standard]",
    "pydantic-settings",
    "orjson",
    "structlog",
    "numpy",
    "pandas",
    "scikit-learn",
    "xgboost",
    "lightgbm",
    "joblib",
]

PRODUCTION_DEV_DEPS = [
    "ruff",
    "pytest",
    "pytest-cov",
    "pyright",
    "httpx",
    "pre-commit",
]


def scaffold(config: InitConfig, runner: UVRunner) -> None:
    runner.init_project(config.project_root, config.slug, config.python_version, config.git)
    _create_structure(config.project_root, config.slug)
    _write_files(config.project_root, config.slug, config.project_name, config.deploy_target)
    runtime_deps = list(PRODUCTION_RUNTIME_DEPS)
    if config.deploy_target == DeployTarget.SERVERLESS:
        runtime_deps.append("mangum")
    runner.add(runtime_deps, cwd=config.project_root)
    runner.add(PRODUCTION_DEV_DEPS, cwd=config.project_root, group="dev")
    _append_pyproject_tooling(config.project_root)
    runner.sync(cwd=config.project_root)
    if config.export_requirements:
        runner.export_requirements(config.project_root, "requirements.txt")
        runner.export_requirements(config.project_root, "requirements-dev.txt", only_dev=True)


def _create_structure(project_root: Path, slug: str) -> None:
    populate_empty_directories(
        [
            project_root / "src" / slug / "api",
            project_root / "src" / slug / "core",
            project_root / "src" / slug / "schemas",
            project_root / "src" / slug / "services",
            project_root / "src" / slug / "model",
            project_root / "tests" / "unit",
            project_root / "tests" / "integration",
            project_root / "models",
        ]
    )


def _write_files(
    project_root: Path,
    slug: str,
    project_name: str,
    deploy_target: DeployTarget | None,
) -> None:
    write_file(project_root / "src" / slug / "__init__.py", production_init_file(slug))
    write_file(project_root / "src" / slug / "main.py", production_main_file())
    write_file(project_root / "src" / slug / "api" / "__init__.py", "")
    write_file(project_root / "src" / slug / "api" / "routes.py", production_routes_file())
    write_file(project_root / "src" / slug / "core" / "__init__.py", "")
    write_file(project_root / "src" / slug / "core" / "config.py", production_config_file())
    write_file(project_root / "src" / slug / "core" / "logging.py", production_logging_file())
    write_file(project_root / "src" / slug / "schemas" / "__init__.py", "")
    write_file(project_root / "src" / slug / "schemas" / "predict.py", production_schemas_file())
    write_file(project_root / "src" / slug / "services" / "__init__.py", "")
    write_file(project_root / "src" / slug / "services" / "predictor.py", production_predictor_file())
    write_file(project_root / "src" / slug / "model" / "__init__.py", "")
    write_file(project_root / "src" / slug / "model" / "loader.py", production_loader_file())
    write_file(project_root / "tests" / "unit" / "test_health.py", production_health_test_file(slug))
    write_file(
        project_root / "tests" / "integration" / "test_predict.py",
        production_predict_test_file(slug),
    )
    write_file(project_root / ".env.example", production_env_example())
    copy_env_example_if_missing(project_root)
    write_file(project_root / ".gitignore", production_gitignore())
    write_file(project_root / "Makefile", production_makefile(slug, deploy_target))
    write_file(project_root / "README.md", production_readme(project_name, slug, deploy_target))

    if deploy_target == DeployTarget.CONTAINER:
        write_file(project_root / "Dockerfile", dockerfile(slug))
        write_file(project_root / ".dockerignore", dockerignore())
        write_file(project_root / "compose.yaml", compose_file(slug))
    elif deploy_target == DeployTarget.SERVERLESS:
        write_file(project_root / "src" / slug / "handler.py", serverless_handler_file())


def _append_pyproject_tooling(project_root: Path) -> None:
    append_block_if_missing(project_root / "pyproject.toml", PRODUCTION_TOOLING)


def production_init_file(slug: str) -> str:
    return f'''from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("{slug}.main:app", host="0.0.0.0", port=8000, reload=True)
'''


def production_main_file() -> str:
    return '''from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from .api.routes import router
from .core.config import get_settings
from .core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        default_response_class=ORJSONResponse,
    )
    app.include_router(router)
    return app


app = create_app()
'''


def production_routes_file() -> str:
    return '''from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas.predict import HealthResponse, PredictRequest, PredictResponse
from ..services.predictor import Predictor, get_predictor_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/predict", response_model=PredictResponse)
def predict(
    payload: PredictRequest,
    predictor: Predictor = Depends(get_predictor_service),
) -> PredictResponse:
    prediction, model_loaded = predictor.predict(payload.features)
    return PredictResponse(prediction=prediction, model_loaded=model_loaded)
'''


def production_config_file() -> str:
    return '''from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Inference API"
    app_env: str = "local"
    log_level: str = "INFO"
    model_path: str = "models/model.joblib"
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
'''


def production_logging_file() -> str:
    return '''from __future__ import annotations

import logging

import structlog


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )
'''


def production_schemas_file() -> str:
    return '''from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class PredictRequest(BaseModel):
    features: dict[str, float] = Field(default_factory=dict)


class PredictResponse(BaseModel):
    prediction: float
    model_loaded: bool
'''


def production_predictor_file() -> str:
    return '''from __future__ import annotations

from functools import lru_cache

from ..core.config import get_settings
from ..model.loader import load_model


class Predictor:
    def __init__(self, model: object) -> None:
        self.model = model

    def predict(self, features: dict[str, float]) -> tuple[float, bool]:
        ordered_values = [value for _, value in sorted(features.items())]
        prediction = self.model.predict([ordered_values])[0]
        model_loaded = getattr(self.model, "model_loaded", True)
        return float(prediction), bool(model_loaded)


@lru_cache
def get_predictor_service() -> Predictor:
    settings = get_settings()
    model = load_model(settings.model_path)
    return Predictor(model)
'''


def production_loader_file() -> str:
    return '''from __future__ import annotations

from pathlib import Path

import joblib


class BaselineModel:
    model_loaded = False

    def predict(self, rows: list[list[float]]) -> list[float]:
        if not rows:
            return [0.0]
        return [float(sum(rows[0]))]


def load_model(model_path: str) -> object:
    path = Path(model_path)
    if not path.exists():
        return BaselineModel()
    return joblib.load(path)
'''


def production_health_test_file(slug: str) -> str:
    return f'''from fastapi.testclient import TestClient

from {slug}.main import app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {{"status": "ok"}}
'''


def production_predict_test_file(slug: str) -> str:
    return f'''from fastapi.testclient import TestClient

from {slug}.main import app
from {slug}.services.predictor import get_predictor_service


class StubPredictor:
    def predict(self, features: dict[str, float]) -> tuple[float, bool]:
        return 7.5, True


def test_predict_returns_prediction() -> None:
    app.dependency_overrides[get_predictor_service] = lambda: StubPredictor()
    client = TestClient(app)

    response = client.post("/predict", json={{"features": {{"feature_a": 1.0}}}})

    assert response.status_code == 200
    assert response.json() == {{"prediction": 7.5, "model_loaded": True}}
    app.dependency_overrides.clear()
'''


def production_env_example() -> str:
    return """APP_NAME=Inference API
APP_ENV=local
LOG_LEVEL=INFO
MODEL_PATH=models/model.joblib
HOST=0.0.0.0
PORT=8000
"""


def production_gitignore() -> str:
    return """.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.DS_Store
.env
models/*
!models/.gitkeep
"""


def production_makefile(slug: str, deploy_target: DeployTarget | None) -> str:
    docker_targets = ""
    if deploy_target == DeployTarget.CONTAINER:
        docker_targets = f"""
docker-build:
\tdocker build -t {slug}:local .

docker-up:
\tdocker compose up --build
"""

    return f"""sync:
\tuv sync

run:
\tuv run uvicorn {slug}.main:app --reload

lint:
\tuv run ruff check .

typecheck:
\tuv run pyright

test:
\tuv run pytest

export:
\tuv export --format requirements.txt --output-file requirements.txt --no-dev --no-emit-project
\tuv export --format requirements.txt --output-file requirements-dev.txt --only-dev --no-emit-project
{docker_targets}"""


def production_readme(project_name: str, slug: str, deploy_target: DeployTarget | None) -> str:
    deploy_section = {
        DeployTarget.CONTAINER: """## Deploy target

Container-first scaffold. Use this when the service will run in Docker-based platforms like ECS,
Kubernetes, Fly.io, Render or a VM-based runtime.
""",
        DeployTarget.SERVERLESS: """## Deploy target

Serverless-first scaffold. Use this when the API will be adapted to a Lambda-style runtime.
The template includes a `Mangum` entrypoint for that path.
""",
        DeployTarget.NEUTRAL: """## Deploy target

Neutral scaffold. The service is production-ready, but deploy artifacts are intentionally omitted.
""",
        None: "",
    }[deploy_target]

    return f"""# {project_name}

Production-ready tabular inference API scaffold.

## Quickstart

```bash
uv sync
uv run uvicorn {slug}.main:app --reload
```

## API surface

- `GET /health`
- `POST /predict`

Request example:

```json
{{
  "features": {{
    "feature_a": 1.0,
    "feature_b": 2.5
  }}
}}
```

{deploy_section}
"""


def dockerfile(slug: str) -> str:
    return f"""FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY .python-version ./

RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "{slug}.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def dockerignore() -> str:
    return """.venv
__pycache__
.pytest_cache
.ruff_cache
.git
"""


def compose_file(slug: str) -> str:
    return f"""services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      APP_ENV: local
      LOG_LEVEL: INFO
    command: uv run uvicorn {slug}.main:app --host 0.0.0.0 --port 8000
"""


def serverless_handler_file() -> str:
    return '''from mangum import Mangum

from .main import app

handler = Mangum(app)
'''


PRODUCTION_TOOLING = """
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[tool.pytest.ini_options]
pythonpath = ["src"]
addopts = "-q"
testpaths = ["tests"]

[tool.pyright]
include = ["src", "tests"]
typeCheckingMode = "basic"
"""

from pathlib import Path

from daten.bootstrap import DeployTarget, TemplateType
from daten.prompts import PromptAdapter, resolve_init_config


class StubPromptAdapter(PromptAdapter):
    def ask_template(self) -> TemplateType:
        return TemplateType.PRODUCTION

    def ask_deploy_target(self) -> DeployTarget:
        return DeployTarget.SERVERLESS


def test_resolve_init_config_uses_prompt_answers_when_missing() -> None:
    config = resolve_init_config(
        project_name="credit-risk",
        base_path=Path("/tmp"),
        prompt_adapter=StubPromptAdapter(),
    )

    assert config.template == TemplateType.PRODUCTION
    assert config.deploy_target == DeployTarget.SERVERLESS
    assert config.slug == "credit_risk"


def test_resolve_init_config_merges_flags_without_prompting() -> None:
    config = resolve_init_config(
        project_name="fraud-api",
        base_path=Path("/tmp"),
        template=TemplateType.PRODUCTION,
        deploy_target=DeployTarget.CONTAINER,
        yes=True,
    )

    assert config.template == TemplateType.PRODUCTION
    assert config.deploy_target == DeployTarget.CONTAINER


def test_resolve_init_config_defaults_to_notebook_in_yes_mode() -> None:
    config = resolve_init_config(project_name="eda", base_path=Path("/tmp"), yes=True)

    assert config.template == TemplateType.NOTEBOOK
    assert config.deploy_target is None

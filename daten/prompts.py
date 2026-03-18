from __future__ import annotations

from pathlib import Path

import questionary

from daten.bootstrap import (
    DeployTarget,
    InitConfig,
    TemplateType,
    resolve_project_root,
    slugify_project_name,
)


class PromptAbortedError(RuntimeError):
    pass


class PromptAdapter:
    def ask_template(self) -> TemplateType:
        answer = questionary.select(
            "Choose the project template",
            choices=[
                questionary.Choice(
                    title="Notebook - EDA, studies and lightweight training",
                    value=TemplateType.NOTEBOOK.value,
                ),
                questionary.Choice(
                    title="Production - tabular inference API",
                    value=TemplateType.PRODUCTION.value,
                ),
            ],
        ).ask()
        if answer is None:
            raise PromptAbortedError("Prompt aborted by user.")
        return TemplateType(answer)

    def ask_deploy_target(self) -> DeployTarget:
        questionary.print(
            "Deploy target guide: container for ECS/Kubernetes/Render/Fly, "
            "serverless for Lambda-style workloads, neutral to skip deploy artifacts."
        )
        answer = questionary.select(
            "Choose the production deploy target",
            choices=[
                questionary.Choice("Container", value=DeployTarget.CONTAINER.value),
                questionary.Choice("Serverless", value=DeployTarget.SERVERLESS.value),
                questionary.Choice("Neutral", value=DeployTarget.NEUTRAL.value),
            ],
        ).ask()
        if answer is None:
            raise PromptAbortedError("Prompt aborted by user.")
        return DeployTarget(answer)


def resolve_init_config(
    project_name: str,
    base_path: Path | str,
    template: TemplateType | None = None,
    python_version: str = "3.12",
    git: bool = True,
    export_requirements: bool = True,
    deploy_target: DeployTarget | None = None,
    yes: bool = False,
    prompt_adapter: PromptAdapter | None = None,
) -> InitConfig:
    adapter = prompt_adapter or PromptAdapter()
    resolved_template = template

    if resolved_template is None:
        resolved_template = TemplateType.NOTEBOOK if yes else adapter.ask_template()

    resolved_deploy_target = deploy_target
    if resolved_template == TemplateType.PRODUCTION and resolved_deploy_target is None:
        resolved_deploy_target = DeployTarget.CONTAINER if yes else adapter.ask_deploy_target()

    return InitConfig(
        project_name=project_name,
        slug=slugify_project_name(project_name),
        project_root=resolve_project_root(base_path, project_name),
        template=resolved_template,
        python_version=python_version,
        git=git,
        export_requirements=export_requirements,
        deploy_target=resolved_deploy_target,
    )

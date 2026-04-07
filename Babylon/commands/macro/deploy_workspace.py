from logging import getLogger
from pathlib import Path as PathlibPath

from click import echo, style

from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.helpers.workspace import (
    create_workspace,
    deploy_postgres_schema,
    update_workspace,
)
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_workspace(namespace: str, file_content: str, deploy_dir: PathlibPath) -> bool:
    echo(style(f"\n🚀 Deploying Workspace in namespace: {env.environ_id}", bold=True, fg="cyan"))

    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)

    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload")
    api_section = state["services"]["api"]
    api_section["workspace_id"] = payload.get("id") or api_section.get("workspace_id", "")
    api_instance = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)

    # --- Deployment Logic ---
    if not api_section["workspace_id"]:
        if not create_workspace(api_instance, api_section, payload, state):
            return CommandResponse.fail()
    else:
        if not update_workspace(api_instance, api_section, payload):
            return CommandResponse.fail()

    # --- PostgreSQL Schema ---
    workspace_id = state["services"]["api"]["workspace_id"]
    spec = content.get("spec") or {}
    schema_config = spec.get("sidecars", {}).get("postgres", {}).get("schema") or {}
    if schema_config.get("create", False):
        deploy_postgres_schema(workspace_id, schema_config, api_section, deploy_dir, state)

    # --- State Persistence ---
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_kubernetes(state)

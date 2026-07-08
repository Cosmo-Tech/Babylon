from logging import getLogger
from pathlib import Path

from click import echo, style

from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.helpers.workspace import (
    _build_dashboard_ext_args,
    deploy_postgres_schema,
)
from Babylon.commands.macro.helpers.workspace.superset_helper import (
    _deploy_or_update_workspace,
    _handle_dashboard_sidecar,
)
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_workspace(namespace: str, file_content: str, deploy_dir: Path) -> bool:
    echo(style(f"\n🚀 Deploying Workspace in namespace: {env.environ_id}", bold=True, fg="cyan"))

    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()

    # Phase 1 render dashboard UUID variables may not exist yet (first deploy).
    # Pass template_content so every {{var}} reference is pre-filled with "" when
    # the key is absent from variables.yaml, preventing strict_undefined crashes.
    pre_ext = _build_dashboard_ext_args(fallback_empty=True, template_content=file_content)
    content = env.fill_template(data=file_content, state=state, ext_args=pre_ext or None)

    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload")
    api_section = state["services"]["api"]
    api_section["workspace_id"] = payload.get("id") or api_section.get("workspace_id", "")
    api_instance = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)

    # --- API Deployment Logic ---
    if not _deploy_or_update_workspace(api_instance, api_section, payload, state):
        return CommandResponse.fail()

    # --- PostgreSQL Schema ---
    workspace_id = state["services"]["api"]["workspace_id"]
    spec = content.get("spec") or {}
    sidecars = spec.get("sidecars", {})
    schema_config = sidecars.get("postgres", {}).get("schema") or {}
    if schema_config.get("create", False):
        deploy_postgres_schema(workspace_id, schema_config, api_section, deploy_dir, state)

    # --- Dashboard Deployment (provider-based dispatch: superset | powerbi) ---
    dashboard_config = sidecars.get("dashboards", {})
    if dashboard_config.get("create", False):
        if not _handle_dashboard_sidecar(dashboard_config, state, config, deploy_dir, api_instance, api_section, file_content):
            return CommandResponse.fail()

    # --- State Persistence ---
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_kubernetes(state)

from logging import getLogger
from pathlib import Path

from click import echo, style

from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.helpers.workspace import (
    _build_dashboard_ext_args,
    deploy_postgres_schema,
)
from Babylon.commands.macro.helpers.workspace.superset_helper import (
    _handle_dashboard_sidecar,
)
from Babylon.commands.macro.helpers.workspace.api_cosmotech_helper import (
    _deploy_or_update_workspace,
)
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.commands.macro.helpers.workspace.api_cosmotech_helper import _get_existing_workspace_id

logger = getLogger(__name__)
env = Environment()


def deploy_workspace(namespace: str, file_content: str, deploy_dir: Path) -> bool:
    echo(style(f"\n🚀 Deploying Workspace in namespace: {env.environ_id}", bold=True, fg="cyan"))

    state = env.retrieve_state_func()

    # Phase 1 render dashboard UUID variables may not exist yet (first deploy).
    # Pass template_content so every {{var}} reference is pre-filled with "" when
    # the key is absent from variables.yaml, preventing strict_undefined crashes.
    pre_ext = _build_dashboard_ext_args(fallback_empty=True, template_content=file_content)
    content = env.fill_template(data=file_content, state=state, ext_args=pre_ext or None)

    keycloak_token, config = get_keycloak_token()

    payload: dict = content.get("spec").get("payload")
    api_section = state["services"]["api"]

    api_instance = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)

    existing_workspace_id, ws_key = _get_existing_workspace_id(state, payload)

    # --- API Deployment Logic ---
    ok, workspace_id = _deploy_or_update_workspace(api_instance, api_section, payload, existing_workspace_id)
    if not ok or not workspace_id:
        return CommandResponse.fail()

    # If workspace_key was not set in variables, fall back to the API-generated workspace_id
    workspace_key: str = payload.get("key", "") or ""
    if not workspace_key:
        ws_key = f"workspace-{workspace_id}"

    # workspace_id lives ONLY in workspaces.<ws_key>.api never in services.api.
    ws_api = state.setdefault("workspaces", {}).setdefault(ws_key, {}).setdefault("api", {})
    ws_api["workspace_id"] = workspace_id

    logger.info(f"  [dim]→ State slot [cyan]{ws_key}[/cyan] updated[/dim]")

    # --- PostgreSQL Schema ---
    spec = content.get("spec") or {}
    sidecars = spec.get("sidecars", {})
    schema_config = sidecars.get("postgres", {}).get("schema") or {}
    if schema_config.get("create", False):
        deploy_postgres_schema(workspace_id, ws_key, schema_config, api_section, deploy_dir, state)

    # --- Dashboard Deployment (provider-based dispatch: superset | powerbi) ---
    dashboard_config = sidecars.get("dashboards", {})
    if dashboard_config.get("create", False):
        if not _handle_dashboard_sidecar(dashboard_config, state, config, deploy_dir, api_instance, api_section, file_content, workspace_id):
            return CommandResponse.fail()

    # --- State Persistence ---
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_kubernetes(state)

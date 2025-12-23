from json import dumps
from logging import getLogger

from click import echo, style
from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_security import WorkspaceSecurity
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest

from Babylon.commands.api.client import get_workspace_api_instance
from Babylon.commands.macro.deploy import update_object_security
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_workspace(namespace: str, file_content: str) -> bool:
    _ret = [""]
    _ret.append("Workspace deployment")
    _ret.append("")
    echo(style("\n".join(_ret), bold=True, fg="green"))
    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    api_section = state["services"]["api"]

    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload")
    spec = {}
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    keycloak_token, config = get_keycloak_token()
    api_instance = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
    if not api_section["workspace_id"]:
        logger.info("Creating workspace")
        workspace_create_request = WorkspaceCreateRequest.from_dict(payload)
        workspace = api_instance.create_workspace(
            organization_id=api_section["organization_id"], workspace_create_request=workspace_create_request
        )
        if workspace is None:
            return CommandResponse.fail()
        logger.info(f"Workspace {workspace.id} successfully created")
        state["services"]["api"]["workspace_id"] = workspace.id
    else:
        workspace_update_request = WorkspaceUpdateRequest.from_dict(payload)
        updated = api_instance.update_workspace(
            organization_id=api_section["organization_id"],
            workspace_id=api_section["workspace_id"],
            workspace_update_request=workspace_update_request,
        )
        if updated is None:
            return CommandResponse.fail()
        if payload.get("security"):
            try:
                current_security = api_instance.get_workspace_security(
                    organization_id=api_section["organization_id"], workspace_id=api_section["workspace_id"]
                )
                update_object_security(
                    "workspace",
                    current_security=current_security,
                    desired_security=WorkspaceSecurity.from_dict(payload.get("security")),
                    api_instance=api_instance,
                    object_id=[api_section["organization_id"], api_section["workspace_id"]],
                )
            except Exception as e:
                logger.error(f"Failed to update workspace security: {e}")
                return CommandResponse.fail()
            logger.info(f"Workspace {api_section['workspace_id']} successfully updated")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)

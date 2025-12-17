from logging import getLogger

from click import command

from Babylon.commands.api.client import (
    get_organization_api_instance,
    get_solution_api_instance,
    get_workspace_api_instance,
)
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_config
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_config
def destroy(config: dict, keycloak_token: str):
    """Macro Destroy"""
    state = env.retrieve_state_func()
    organization_id = state["services"]["api"]["organization_id"]
    workspace_id = state["services"]["api"]["workspace_id"]
    solution_id = state["services"]["api"]["solution_id"]

    organization_api_instance = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
    workspace_api_instance = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
    solution_api_instance = get_solution_api_instance(config=config, keycloak_token=keycloak_token)

    if solution_id:
        try:
            solution_api_instance.delete_solution(organization_id=organization_id, solution_id=solution_id)
            logger.info(f"Deleted solution {solution_id}")
            state["services"]["api"]["solution_id"] = ""
        except Exception as e:
            logger.error(f"Error deleting solution {solution_id}: {e}")
    if workspace_id:
        try:
            workspace_api_instance.delete_workspace(organization_id=organization_id, workspace_id=workspace_id)
            logger.info(f"Deleting workspace {workspace_id}")
            state["services"]["api"]["workspace_id"] = ""
        except Exception as e:
            logger.error(f"Error deleting workspace {workspace_id}: {e}")
    if organization_id:
        try:
            organization_api_instance.delete_organization(organization_id=organization_id)
            logger.info(f"Deleted organization {organization_id}")
            state["services"]["api"]["organization_id"] = ""
        except Exception as e:
            logger.error(f"Error deleting organization {organization_id}: {e}")
    env.store_state_in_local(state=state)
    if env.remote:
        env.store_state_in_cloud(state=state)
    return CommandResponse.success()

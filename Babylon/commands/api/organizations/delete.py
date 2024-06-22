from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def delete(state: Any, azure_token: str, organization_id: str, force_validation: bool = False) -> CommandResponse:
    """Delete an organization"""
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service = OrganizationService(state=service_state, azure_token=azure_token)
    response = service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    if response:
        org_id = service_state["api"]["organization_id"]
        logger.info(f'Organization {org_id} successfully deleted')
        if org_id == state["services"]["api"]["organization_id"]:
            state["services"]["api"]["organization_id"] = ""
            env.store_state_in_local(state)
            if env.remote:
                env.store_state_in_cloud(state)
            logger.info(f'Organization {org_id} successfully deleted in state {state.get("id")}')
    return CommandResponse.success()

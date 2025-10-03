import click

from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def delete(state: Any, keycloak_token: str, organization_id: str, force_validation: bool = False) -> CommandResponse:
    """Delete an organization"""
    _ret = [""]
    _ret.append("Delete organization")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    state['services']["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service = OrganizationService(state=state['services'], keycloak_token=keycloak_token)
    logger.info("[api] Deleting organization")
    response = service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    org_id = state['services']["api"]["organization_id"]
    logger.info(f"[api] Organization {org_id} successfully deleted")
    state["services"]["api"]["organization_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success()

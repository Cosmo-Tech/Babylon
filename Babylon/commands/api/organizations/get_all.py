import jmespath
import json
import click

from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, keycloak_token: str, filter: str) -> CommandResponse:
    """
    Get all organizations details
    """
    _ret = [""]
    _ret.append("Get all organizations details")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    organization_service = OrganizationService(state=state['services'], keycloak_token=keycloak_token)
    logger.info("[api] Retrieving all organizations details")
    response = organization_service.get_all()
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    if len(organizations) and filter:
        organizations = jmespath.search(filter, organizations)
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(json.dumps(organizations, indent=2))
    return CommandResponse.success()

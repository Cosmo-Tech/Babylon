from logging import getLogger
from typing import Any
from click import Context, argument, option, pass_context
from click import command
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.services.organizations_service import OrganizationsService

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--select", "select", is_flag=True, default=True, help="Save this organization in configuration")
@argument("id", type=QueryType(), required=False)
@retrieve_state
def get(ctx: Context, state: Any, id: str, azure_token: str, select: bool) -> CommandResponse:
    """Get an organization details"""
    organizations_service = OrganizationsService(state, azure_token)
    response = organizations_service.get(ctx)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="organization_id",
                                  var_value=organization["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("api", "organization_id"))
    return CommandResponse.success(organization, verbose=True)

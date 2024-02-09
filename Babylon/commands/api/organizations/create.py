import pathlib

from logging import getLogger
from typing import Any, Optional
from click import Context, argument, pass_context
from click import command
from click import option
from click import Path
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED, SUCCESS_CREATED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
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
@option("--email", "security_id", type=QueryType(), help="Email valid")
@option("--role", "security_role", type=QueryType(), default="admin", required=True, help="Role RBAC")
@option("--file",
        "org_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom organization description file (yaml or json)")
@option("--select", "select", is_flag=True, default=True, help="Save this new organization in configuration")
@argument("name", type=QueryType())
@retrieve_state
def create(
    ctx: Context,
    state: Any,
    azure_token: str,
    name: str,
    security_id: str,
    security_role: str,
    select: bool,
    org_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Register new orgnanization
    """
    organizations_service = OrganizationsService(state, azure_token)
    response = organizations_service.create(name, security_id, security_role, org_file)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="organization_id",
                                  var_value=organization["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("organizations", organization["id"]))
    logger.info(SUCCESS_CREATED("organizations", organization["id"]))
    return CommandResponse.success(organization, verbose=True)

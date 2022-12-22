import logging

from azure.core.credentials import AccessToken
from click import Context
from click import command
from click import argument
from click import pass_context
from click import option

from ......utils.decorators import output_to_file
from ......utils.logging import table_repr
from ......utils.typing import QueryType
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("workspace_name", type=QueryType())
@option("-s",
        "--select",
        "select",
        is_flag=True,
        help="Select this new Organization as one of babylon context Organizations ?",
        default=False)
@output_to_file
def create(ctx: Context, workspace_name: str, select: bool) -> CommandResponse:
    """Create workspace named WORKSPACE_NAME into Power Bi App"""
    env = Environment()
    access_token = ctx.find_object(AccessToken).token
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups?$workspaceV2=True'
    response = oauth_request(url=url_groups, access_token=access_token, json_data={"name": workspace_name}, type="POST")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info("\n".join(table_repr([
        output_data,
    ])))
    if select:
        env.configuration.set_deploy_var(
            "powerbi_workspace_id",
            output_data["id"],
        )  # May return environnement error
    return CommandResponse(data=output_data)

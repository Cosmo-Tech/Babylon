import json
import logging

from azure.core.credentials import AccessToken
from click import Context
from click import command
from click import argument
from click import pass_context

from ......utils.decorators import output_to_file
from ......utils.logging import table_repr
from ......utils.typing import QueryType
from ......utils.response import CommandResponse
from ......utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("workspace_name", type=QueryType())
@output_to_file
def create(ctx: Context, workspace_name: str) -> CommandResponse:
    """Create workspace named WORKSPACE_NAME into Power Bi App"""
    access_token = ctx.find_object(AccessToken).token
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups?$workspaceV2=True'
    response = oauth_request(url=url_groups,
                             access_token=access_token,
                             data=json.dumps({"name": workspace_name}),
                             type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info("\n".join(table_repr([
        response,
    ])))
    return CommandResponse(data=response)

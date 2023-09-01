import logging

from typing import Any
from click import command, option, pass_context
from click import argument
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_context
@output_to_file
@pass_azure_token("graph")
@option("--select", "select", is_flag=True, default=True, help="Save this app in configuration")
@argument("object_id", type=QueryType())
def get_principal(ctx: Any, azure_token: str, select: bool, object_id: str) -> CommandResponse:
    """
    Get an app registration service principal
    https://learn.microsoft.com/en-us/graph/api/serviceprincipal-get
    """
    get_route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
    get_response = oauth_request(get_route, azure_token)
    if get_response is None:
        return CommandResponse.fail()
    app_id = get_response.json().get("appId")
    route = f"https://graph.microsoft.com/v1.0/servicePrincipals(appId='{app_id}')"
    response = oauth_request(route, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if select:
        r_id = ctx.parent.command.name
        env.configuration.set_var(resource_id=r_id, var_name="principal_id", var_value=output_data["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("app", "principal_id"))
    return CommandResponse.success(output_data, verbose=True)

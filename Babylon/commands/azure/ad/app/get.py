import logging
import polling2

from click import Context, command, option, pass_context
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
@argument("object_id", type=QueryType())
@option("--select", "select", is_flag=True, default=True, help="Save this app in configuration")
def get(
    ctx: Context,
    azure_token: str,
    object_id: str,
    select: bool,
) -> CommandResponse:
    """
    Get an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-get
    """
    route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
    response = polling2.poll(lambda: oauth_request(route, azure_token),
                             check_success=is_correct_response,
                             step=1,
                             timeout=60)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if select:
        r_id = ctx.parent.command.name
        env.configuration.set_var(resource_id=r_id, var_name="app_id", var_value=output_data["appId"])
        logger.info(SUCCESS_CONFIG_UPDATED("app", "app_id"))
        env.configuration.set_var(resource_id=r_id, var_name="name", var_value=output_data["displayName"])
        logger.info(SUCCESS_CONFIG_UPDATED("app", "name"))
        env.configuration.set_var(resource_id=r_id, var_name="object_id", var_value=object_id)
        logger.info(SUCCESS_CONFIG_UPDATED("app", "object_id"))
    return CommandResponse.success(output_data, verbose=True)


def is_correct_response(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if "id" in output_data:
        return True

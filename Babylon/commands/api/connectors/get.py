from logging import getLogger
from typing import Any
from click import Choice, Context, argument, option, pass_context
from click import command
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_context
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--select", "select", is_flag=True, default=True, help="Save this connector in configuration")
@option("--type",
        "type",
        type=Choice(["adt", "storage", "twin"]),
        required=True,
        help="Connector type Cosmotech Platform")
@argument("id", type=QueryType())
@inject_context_with_resource({'api': ['url']})
def get(ctx: Context, context: Any, azure_token: str, id: str, type: str, select: bool = False) -> CommandResponse:
    """Get a registered connector details"""
    _type = type.lower()
    response = oauth_request(f"{context['api_url']}/connectors/{id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    connector = response.json()

    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name=["connector", f"{_type}_id"],
                                  var_value=connector['id'])
        logger.info(SUCCESS_CONFIG_UPDATED("api", f"connector.{type}_id"))
    return CommandResponse.success(connector, verbose=True)

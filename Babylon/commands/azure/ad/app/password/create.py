import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.ad.app.password.service.api import (
    AzureDirectoyPasswordService,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token("graph")
@option("--name", "password_name", type=QueryType(), help="Password display name")
@option(
    "--object-id",
    "object_id",
    type=QueryType(),
    help="Object Id Azure App Registration",
)
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    object_id: str,
    password_name: Optional[str] = None,
) -> CommandResponse:
    """
    Register a password or secret to an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-addpassword
    """
    service = AzureDirectoyPasswordService(azure_token=azure_token, state=state)
    response = service.create(
        object_id=object_id,
        password_name=password_name,
    )
    return CommandResponse.success(response, verbose=True)

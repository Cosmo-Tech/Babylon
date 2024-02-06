import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.azure.ad.app.password.service.api import (
    AzureDirectoyPasswordService,
)
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

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
@inject_context_with_resource(
    {"api": ["organization_id", "workspace_key"], "app": ["object_id", "name"]}
)
def create(
    context: Any,
    azure_token: str,
    object_id: str,
    password_name: Optional[str] = None,
) -> CommandResponse:
    """
    Register a password or secret to an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-addpassword
    """
    apiPass = AzureDirectoyPasswordService(azure_token=azure_token, state=context)
    response = apiPass.create(
        object_id=object_id,
        password_name=password_name,
    )
    return CommandResponse.success(response, verbose=True)

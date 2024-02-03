import logging

from typing import Any
from click import Choice, command, option
from Babylon.commands.azure.token.service.api import AzureTokenService
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext


logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@option("--email", "email", help="User email")
@option(
    "--scope",
    "scope",
    type=Choice(["default", "powerbi", "graph"]),
    required=True,
    help="API Scope",
)
@inject_context_with_resource({"azure": ["user_principal_id", "cli_client_id"]})
def store(context: Any, scope: str, email: str) -> CommandResponse:
    """
    Store a refresh token using a secret key
    """
    api_token = AzureTokenService(context=context)
    api_token.store(email=email, scope=scope)
    return CommandResponse.success()

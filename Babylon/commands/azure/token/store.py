import logging

from typing import Any
from click import Choice, command, option
from Babylon.commands.azure.token.services.api import AzureTokenService
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, injectcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@option("--email", "email", help="User email")
@option(
    "--scope",
    "scope",
    type=Choice(["default", "powerbi", "graph"]),
    required=True,
    help="API Scope",
)
@retrieve_state
def store(state: Any, scope: str, email: str) -> CommandResponse:
    """
    Store a refresh token using a secret key
    """
    service_state = state['services']
    service = AzureTokenService(state=service_state)
    service.store(email=email, scope=scope)
    return CommandResponse.success()

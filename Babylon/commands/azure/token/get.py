import logging
from typing import Any

from click import Choice, command, option

from Babylon.commands.azure.token.services.token_api_svc import AzureTokenService
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@option("-e", "--email", "email", help="User email")
@option(
    "--scope",
    "scope",
    type=Choice(["default", "powerbi", "graph"]),
    required=True,
    help="API Scope",
)
@retrieve_state
def get(state: Any, scope: str, email: str) -> CommandResponse:
    """
    Get un acces token using a secret key
    """
    service_state = state["services"]
    service = AzureTokenService(state=service_state)
    response = service.get(email=email, scope=scope)
    return CommandResponse.success(response, verboser=True)

import logging

from click import Choice, command, option
from Babylon.commands.azure.token.service.api import AzureTokenService
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

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
def get(scope: str, email: str) -> CommandResponse:
    """
    Get un acces token using a secret key
    """
    api_token = AzureTokenService()
    response = api_token.get(email=email, scope=scope)
    return CommandResponse.success(response, verboser=True)

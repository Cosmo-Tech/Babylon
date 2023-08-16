import logging

from click import Choice, command, option
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@option("--email", "email", help="User email")
@option("--scope", "scope", type=Choice(['default', "powerbi", "graph"]), required=True, help="API Scope")
def get(scope: str, email: str) -> CommandResponse:
    """
    Get un acces token using a secret key
    """
    email = email or env.configuration.get_var(resource_id="azure", var_name="email")
    access_token = env.get_access_token_with_refresh_token(username=email, internal_scope=scope)
    if access_token:
        print(access_token)
    return CommandResponse.success()

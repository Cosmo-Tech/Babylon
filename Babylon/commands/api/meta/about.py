import json
from click import command, echo, style
from logging import getLogger
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_state
def about(state: dict, keycloak_token: str) -> dict:
    """
    Get the version of the API service
    """
    _meta = [""]
    _meta.append("Get the version of the API service")
    _meta.append("")
    echo(style("\n".join(_meta), bold=True, fg="green"))
    url = state.get("services").get("api").get("url")
    if not url:
        logger.error("[babylon] Api url not found verify the state")
        return CommandResponse.fail()
    response = oauth_request(f"{url}/about", keycloak_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    info = response.json()
    logger.info(json.dumps(info, indent=2))
    return CommandResponse.success(info)

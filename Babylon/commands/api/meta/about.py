from logging import getLogger

from click import command, echo, style

from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
def about(config: dict, keycloak_token: str) -> dict:
    """
    Get the version of the API service
    """
    _meta = [""]
    _meta.append("Get the version of the API service")
    _meta.append("")
    echo(style("\n".join(_meta), bold=True, fg="green"))
    url = config["api_url"]
    if not url:
        logger.error("api url not found verify the config in the k8s secret")
        return CommandResponse.fail()
    response = oauth_request(f"{url}/about", keycloak_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    info = response.json()
    logger.info(f"API version:{info.get('version')}")
    return CommandResponse.success(info)

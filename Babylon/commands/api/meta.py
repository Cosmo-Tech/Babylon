from logging import getLogger

from click import command
from cosmotech_api import ApiClient, Configuration, MetaApi
from cosmotech_api.models.about_info import AboutInfo

from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_meta_api_instance(config: dict, keycloak_token: str) -> MetaApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return MetaApi(api_client)


def get_about_info(api_url: str, keycloak_token: str) -> dict:
    """
    Pure function: retrieve API 'about' information.

    This function contains no Click or CLI dependencies and can be safely
    imported and called by any external application (e.g. a FastAPI service).

    Returns:
        A plain Python dictionary with the API about information.

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    api_instance = get_meta_api_instance({"api_url": api_url}, keycloak_token)
    logger.info("  [dim]→ Sending request to API...[/dim]")
    try:
        about_info: AboutInfo = api_instance.about()
    except Exception as e:
        raise RuntimeError(f"Could not retrieve about information: {e}") from e
    logger.info(f"  [green]✔[/green] API About Information: {about_info}")
    return about_info.to_dict()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
def about(config: dict, keycloak_token: str) -> CommandResponse:
    """Get API about information"""
    try:
        data = get_about_info(api_url=config.get("api_url"), keycloak_token=keycloak_token)
        return CommandResponse.success(data)
    except RuntimeError as e:
        logger.error(f"  [bold red]✘[/bold red] {e}")
        return CommandResponse.fail()

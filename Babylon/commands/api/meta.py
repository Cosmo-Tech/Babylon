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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
def about(config: dict, keycloak_token: str) -> CommandResponse:
    """Get API about information"""
    api_instance = get_meta_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        about_info: AboutInfo = api_instance.about()
        logger.info(f"  [green]✔[/green] API About Information: {about_info}")
        return CommandResponse.success(about_info.to_dict())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not retrieve about information: {e}")
        return CommandResponse.fail()

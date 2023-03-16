import logging
import pathlib

from click import command
from click import argument
from click import Path
from click import option
from rich.pretty import pretty_repr

from .....utils.environment import Environment
from .....utils.request import oauth_request
from .....utils.decorators import require_platform_key
from .....utils.response import CommandResponse
from .....utils.credentials import pass_azure_token
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name", type=QueryType())
@option("-f", "--file", "settings_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
def update(azure_token: str, azure_subscription: str, resource_group_name: str, webapp_name: str,
           settings_file: pathlib.Path) -> CommandResponse:
    """
    Update static webapp app settings in the given webapp
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    env = Environment()
    settings_file = settings_file or env.working_dir.payload_path / "webapp/webapp_settings.json"
    details = env.fill_template(settings_file)
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/config/appsettings?api-version=2022-03-01",
        azure_token,
        type="PUT",
        data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully launched creation of webapp {webapp_name} settings from file {settings_file}")
    return CommandResponse.success(output_data)
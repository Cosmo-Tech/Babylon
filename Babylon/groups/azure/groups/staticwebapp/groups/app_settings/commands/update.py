import logging
import pathlib

from click import command
from click import argument
from click import Path
from click import option
from rich.pretty import pretty_repr

from ........utils.environment import Environment
from ........utils.request import oauth_request
from ........utils.decorators import require_platform_key
from ........utils.response import CommandResponse
from ........utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")

DEFAULT_PAYLOAD_TEMPLATE = ".payload_templates/webapp/webapp_settings.json"


@command()
@pass_azure_token("powerbi")
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name")
@option("-f", "--file", "settings_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def update(azure_token: str,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           settings_file: pathlib.Path,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Update static webapp app settings in the given webapp
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    env = Environment()
    settings_file = settings_file or env.working_dir.get_file(DEFAULT_PAYLOAD_TEMPLATE)
    details = env.fill_template(settings_file, use_working_dir_file=use_working_dir_file)
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

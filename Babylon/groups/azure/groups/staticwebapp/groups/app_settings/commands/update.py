import logging
import pathlib
from string import Template

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import argument
from click import Path
from click import option
from rich.pretty import pretty_repr

from ........utils.environment import Environment
from ........utils.request import oauth_request
from ........utils.decorators import require_platform_key
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name")
@option("-f",
        "--file",
        "settings_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        required=True)
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def update(ctx: Context,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           settings_file: str,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Update static webapp app settings in the given webapp
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    access_token = ctx.find_object(AccessToken).token
    env = Environment()
    if use_working_dir_file:
        settings_file = env.working_dir.get_file(str(settings_file))
    details = ""
    with open(settings_file, "r") as _file:
        template = _file.read()
        data = {**env.configuration.get_deploy(), **env.configuration.get_platform()}
        try:
            details = Template(template).substitute(data)
        except Exception as e:
            logger.error(f"Could not fill parameters template: {e}")
            return CommandResponse.fail()
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/config/appsettings?api-version=2022-03-01",
        access_token,
        type="PUT",
        data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully launched creation of webapp {webapp_name} settings from file {settings_file}")
    return CommandResponse.success(output_data)
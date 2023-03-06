import logging
import pathlib
from string import Template
from typing import Optional

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

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name")
@argument("domain_name")
@option("-f", "--file", "create_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def create(azure_token: str,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           domain_name: str,
           create_file: Optional[str] = None,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Create a static webapp custom domain in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site-custom-domain
    """
    env = Environment()
    create_route = (
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01")
    if use_working_dir_file:
        create_file = env.working_dir.get_file(str(create_file))
    details = '{"properties":{}}'
    if create_file:
        with open(create_file, "r") as _file:
            template = _file.read()
            data = {**env.configuration.get_deploy(), **env.configuration.get_platform()}
            try:
                details = Template(template).substitute(data)
            except Exception as e:
                logger.error(f"Could not fill parameters template: {e}")
                return CommandResponse.fail()
    response = oauth_request(create_route, azure_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully launched creation of custom domain {domain_name} for webapp {webapp_name}")
    return CommandResponse.success(output_data)

import logging
import pathlib
from typing import Optional

from click import command
from click import argument
from click import Path
from click import option
from rich.pretty import pretty_repr

from ....utils.environment import Environment
from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.response import CommandResponse
from ....utils.credentials import pass_azure_token
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")

DEFAULT_PAYLOAD_TEMPLATE = ".payload_templates/webapp/webapp_details.json"


@command()
@pass_azure_token()
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name", type=QueryType())
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
           create_file: Optional[Path] = None,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Create a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    env = Environment()
    create_file = create_file or env.working_dir.get_file(DEFAULT_PAYLOAD_TEMPLATE)
    details = env.fill_template(create_file, use_working_dir_file=use_working_dir_file)
    route = (f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
             f"providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01")
    response = oauth_request(route, azure_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully launched creation of webapp {webapp_name} in resource group {resource_group_name}")
    return CommandResponse.success(output_data)

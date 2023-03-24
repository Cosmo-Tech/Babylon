import logging
import pathlib
from typing import Optional

from click import command
from click import argument
from click import Path
from click import option

from ....utils.environment import Environment
from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.response import CommandResponse
from ....utils.credentials import pass_azure_token
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token()
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name", type=QueryType())
@option("-f", "--file", "swa_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
def create(azure_token: str,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           swa_file: Optional[Path] = None) -> CommandResponse:
    """
    Create a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    env = Environment()
    swa_file = swa_file or env.working_dir.payload_path / "webapp/webapp_details.json"
    details = env.fill_template(swa_file)
    route = (f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
             f"providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01")
    response = oauth_request(route, azure_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(f"Successfully launched creation of webapp {webapp_name} in resource group {resource_group_name}")
    return CommandResponse.success(output_data, verbose=True)

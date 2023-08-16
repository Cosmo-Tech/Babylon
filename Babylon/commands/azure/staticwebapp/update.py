import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import option
from click import pass_context
from click import Context
from click import Path
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_context
@pass_azure_token()
@option("-f", "--file", "swa_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def update(ctx: Context,
           context: Any,
           azure_token: str,
           webapp_name: str,
           swa_file: Optional[Path] = None) -> CommandResponse:
    """
    Update a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    swa_file = swa_file or env.working_dir.original_template_path / "webapp/webapp_details.json"
    github_secret = env.get_global_secret(resource="github", name="token")
    details = env.fill_template(swa_file, data={"secrets_github_token": github_secret})
    route = (f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
             f"providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01")
    response = oauth_request(route, azure_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info("Successfully launched")
    return CommandResponse.success(output_data, verbose=True)

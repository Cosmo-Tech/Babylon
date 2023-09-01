import logging
import pathlib
from typing import Any, Optional

from click import command, pass_context
from click import argument
from click import Path
from click import option
from Babylon.utils.checkers import check_ascii

from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_context
@pass_azure_token()
@option("--file", "swa_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("--select", "select", is_flag=True, default=True, help="Save this new staticwebapp in your configuration")
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def create(ctx: Any,
           context: Any,
           azure_token: str,
           webapp_name: str,
           select: bool,
           swa_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """
    Create a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    check_ascii(webapp_name)
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
    logger.info(
        f"Successfully launched {ctx.command.name} of webapp {webapp_name} in resource group {resource_group_name}")
    if select:
        env.configuration.set_var(resource_id="webapp",
                                  var_name="static_domain",
                                  var_value=output_data['properties']['defaultHostname'])
        logger.info(SUCCESS_CONFIG_UPDATED("webapp", "static_domain"))
        env.configuration.set_var(resource_id="webapp",
                                  var_name="hostname",
                                  var_value=output_data['properties']['defaultHostname'].split(".")[0])
        logger.info(SUCCESS_CONFIG_UPDATED("webapp", "hostname"))
    return CommandResponse.success(output_data, verbose=True)

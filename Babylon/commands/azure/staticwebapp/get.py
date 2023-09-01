import logging
import polling2
from typing import Any

from click import command, option
from click import argument
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED

from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option("--select", "select", is_flag=True, default=True, help="Save this new connector in your configuration")
@argument("name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def get(context: Any, azure_token: str, select: bool, name: str) -> CommandResponse:
    """
    Get static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site
    """
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    response = polling2.poll(lambda: oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
        f"/providers/Microsoft.Web/staticSites/{name}?api-version=2022-03-01", azure_token),
                             check_success=is_correct_response,
                             step=1,
                             timeout=60)
    if response is None:
        return CommandResponse.fail(verbose=False)

    if select:
        outputdata = response.json()
        env.configuration.set_var(resource_id="webapp",
                                  var_name="deployment_name",
                                  var_value=outputdata['name'].replace("WebApp", ""))
        logger.info(SUCCESS_CONFIG_UPDATED("webapp", "deployment_name"))
        env.configuration.set_var(resource_id="webapp",
                                  var_name="static_domain",
                                  var_value=outputdata['properties']['defaultHostname'])
        logger.info(SUCCESS_CONFIG_UPDATED("webapp", "static_domain"))
    return CommandResponse.success(outputdata, verbose=True)


def is_correct_response(response):
    if response is None:
        return " "
    output_data = response.json()
    if "id" in output_data:
        return output_data

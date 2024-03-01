import logging
from typing import Any

from click import command, argument
from Babylon.utils.decorators import inject_context_with_resource, injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger('Babylon')


@command()
@injectcontext()
@pass_azure_token()
@argument('powerbi_name', type=QueryType())
@inject_context_with_resource({'azure': ['subscription_id', 'resource_group_name']})
def resume(context: Any, azure_token: str, powerbi_name: str) -> CommandResponse:
    """
    Resume a PowerBI Service
    """
    subscription_id = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    route = (f'https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.PowerBIDedicated/capacities/{powerbi_name}/resume?api-version=2021-01-01')

    response = oauth_request(route, azure_token, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully resumed {powerbi_name} instance !"
                f"in resource group {resource_group_name}")
    return CommandResponse.success(response, verbose=True)

import logging

from click import command, argument

from ...utils.response import CommandResponse
from ...utils.request import oauth_request
from ...utils.decorators import require_platform_key
from ...utils.credentials import pass_azure_token
from ...utils.typing import QueryType

logger = logging.getLogger('Babylon')


@command()
@pass_azure_token()
@require_platform_key('azure_subscription')
@require_platform_key('resource_group_name')
@argument('powerbi_name', type=QueryType())
def resume(azure_token: str,
           azure_subscription: str,
           resource_group_name: str,
           powerbi_name: str) -> CommandResponse:

    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.PowerBIDedicated/capacities/{powerbi_name}/resume?api-version=2021-01-01')

    response = oauth_request(route, azure_token, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully resumed {powerbi_name} instance !"
                f"in resource group {resource_group_name}")
    return CommandResponse.success(response, verbose=True)

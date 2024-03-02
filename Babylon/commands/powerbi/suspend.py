import logging

from click import command, argument

from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger('Babylon')


@command()
@injectcontext()
@pass_azure_token()
@argument('powerbi_name', type=str)
@retrieve_state
def suspend(state: dict, azure_token: str, powerbi_name: str) -> CommandResponse:
    """
    Suspend a PowerBI Service
    """
    subscription_id = state['services']['azure']['subscription_id']
    resource_group_name = state['services']['azure']['resource_group_name']
    route = (f'https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.PowerBIDedicated/capacities/{powerbi_name}/suspend?api-version=2021-01-01')

    response = oauth_request(route, azure_token, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully suspended {powerbi_name} instance !"
                f"in resource group {resource_group_name}")
    return CommandResponse.success(response, verbose=True)

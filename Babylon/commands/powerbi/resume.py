import logging

from click import command, argument
<<<<<<< HEAD
from Babylon.utils.decorators import injectcontext, retrieve_state
=======
from Babylon.utils.decorators import inject_context_with_resource, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_azure_token
<<<<<<< HEAD
=======

>>>>>>> cb4637b4 (remove querytype)

logger = logging.getLogger('Babylon')


@command()
@injectcontext()
@pass_azure_token()
@argument('powerbi_name', type=str)
@retrieve_state
def resume(state: dict, azure_token: str, powerbi_name: str) -> CommandResponse:
    """
    Resume a PowerBI Service
    """
    subscription_id = state['services']['azure']['subscription_id']
    resource_group_name = state['services']['azure']['resource_group_name']
    route = (f'https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.PowerBIDedicated/capacities/{powerbi_name}/resume?api-version=2021-01-01')

    response = oauth_request(route, azure_token, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully resumed {powerbi_name} instance !"
                f"in resource group {resource_group_name}")
    return CommandResponse.success(response, verbose=True)

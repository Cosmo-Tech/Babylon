import logging

from click import argument
from click import command
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_adt_management_client


logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_adt_management_client
@argument("name", type=str)
@retrieve_state
def get(state: dict, adt_management_client: AzureDigitalTwinsManagementClient, name: str) -> CommandResponse:
    """
    Get an azure digital twins instance details
    """
    try:
        instance = adt_management_client.digital_twins.get(state['services']['azure']['resource_group_name'], name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to get ADT instance '{name}': {error_message[0]}")
        return CommandResponse.fail()
    return CommandResponse.success(instance.as_dict(), verbose=True)

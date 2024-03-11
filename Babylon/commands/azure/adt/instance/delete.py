import logging

from click import argument
from click import command
from click import option
from typing import Optional
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_adt_management_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_adt_management_client
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("name", type=str)
@retrieve_state
def delete(state: dict,
           adt_management_client: AzureDigitalTwinsManagementClient,
           name: str,
           force_validation: Optional[bool] = False) -> CommandResponse:
    """
    Delete a ADT instance in current platform resource group
    """
    resource_group_name = state['services']['azure']['resource_group_name']
    if not force_validation and not confirm_deletion("instance", name):
        return CommandResponse.fail()

    logger.info(f"Deleting Adt instance {name}")
    try:
        poller = adt_management_client.digital_twins.begin_delete(resource_group_name, name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to create ADT instance '{name}': {error_message[0]}")
        return CommandResponse.fail()
    # waits for completion.
    poller.wait()
    if not poller.done():
        return CommandResponse.fail()
    adt_deletion_result = poller.result()
    logger.info("Successfully deleted")
    return CommandResponse.success({"name": adt_deletion_result.name})

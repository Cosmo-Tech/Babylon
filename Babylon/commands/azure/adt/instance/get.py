import logging

from typing import Any
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import argument
from click import command
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_adt_management_client
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@output_to_file
@pass_adt_management_client
@argument("name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name']})
def get(context: Any, adt_management_client: AzureDigitalTwinsManagementClient, name: str) -> CommandResponse:
    """
    Get an azure digital twins instance details
    """
    try:
        instance = adt_management_client.digital_twins.get(context['azure_resource_group_name'], name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to get ADT instance '{name}': {error_message[0]}")
        return CommandResponse.fail()
    return CommandResponse.success(instance.as_dict(), verbose=True)

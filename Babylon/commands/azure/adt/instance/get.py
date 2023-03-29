import logging
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import argument
from click import command

from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator
from .....utils.decorators import output_to_file
from .....utils.response import CommandResponse
from .....utils.clients import pass_adt_management_client
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_adt_management_client
@timing_decorator
@require_platform_key("resource_group_name")
@argument("adt_instance_name", type=QueryType())
@output_to_file
def get(adt_management_client: AzureDigitalTwinsManagementClient, resource_group_name: str,
        adt_instance_name: str) -> CommandResponse:
    """Get an azure digital twins instance details"""
    try:
        instance = adt_management_client.digital_twins.get(resource_group_name, adt_instance_name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to get ADT instance '{adt_instance_name}': {error_message[0]}")
        return CommandResponse.fail()
    return CommandResponse.success(instance.as_dict(), verbose=True)

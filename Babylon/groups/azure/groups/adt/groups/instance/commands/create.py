import logging

from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import argument
from click import command

from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator
from ........utils.response import CommandResponse
from ........utils.clients import pass_adt_management_client

logger = logging.getLogger("Babylon")


@command()
@pass_adt_management_client
@argument("adt_instance_name")
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("resources_location", "resources_location")
@timing_decorator
def create(
    adt_management_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    resources_location: str,
    adt_instance_name: str,
) -> CommandResponse:
    """Create a new ADT instance in current platform resource group"""

    availability_result = adt_management_client.digital_twins.check_name_availability(
        digital_twins_instance_check_name={
            "name": adt_instance_name,
            "type": "Microsoft.DigitalTwins/digitalTwinsInstances"
        },
        location=resources_location,
    )

    if not availability_result.name_available:
        logger.info(availability_result.message)
        return CommandResponse.fail()

    try:
        poller = adt_management_client.digital_twins.begin_create_or_update(
            resource_group_name,
            adt_instance_name,
            {
                "location": resources_location,
                "tags": {
                    "creator": "babylon"
                }
            },
        )
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to create ADT instance '{adt_instance_name}': {error_message[0]}")
        return CommandResponse.fail()

    # Long-running operations return a poller object; calling poller.result()
    # waits for completion.
    adt_creation_result = poller.result()
    logger.info(f"Provisioned digital twins instance {adt_creation_result.name}")
    return CommandResponse.success({"name": adt_creation_result.name})

import logging
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import argument
from click import command
from click import make_pass_decorator

from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")

pass_digital_twins_client = make_pass_decorator(AzureDigitalTwinsManagementClient)


@command()
@pass_digital_twins_client
@argument("adt_instance_name")
@require_platform_key("resource_group_name")
@require_platform_key("resources_location")
@timing_decorator
def create(
    digital_twins_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    resources_location: str,
    adt_instance_name: str,
) -> Optional[str]:
    """Create a new ADT instance in current platform resource group"""

    availability_result = digital_twins_client.digital_twins.check_name_availability(
        digital_twins_instance_check_name={
            "name": adt_instance_name,
            "type": "Microsoft.DigitalTwins/digitalTwinsInstances"
        },
        location=resources_location,
    )

    if not availability_result.name_available:
        logger.info(availability_result.message)
        return

    try:
        poller = digital_twins_client.digital_twins.begin_create_or_update(
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
        return

    # Long-running operations return a poller object; calling poller.result()
    # waits for completion.
    adt_creation_result = poller.result()
    logger.info(f"Provisioned digital twins instance {adt_creation_result.name}")
    return adt_creation_result.name

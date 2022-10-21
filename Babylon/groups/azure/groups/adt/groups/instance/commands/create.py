import logging

from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import command
from click import make_pass_decorator
from click import option

from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")

pass_digital_twins_client = make_pass_decorator(AzureDigitalTwinsManagementClient)


@command()
@pass_digital_twins_client
@option(
    "-n",
    "--name",
    "instance_name",
    required=False,
    type=str,
    help="New instance name",
)
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("resources_location", "resources_location")
def create(
    digital_twins_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    resources_location: str,
    instance_name: str,
):
    """Command created from a template"""

    availability_result = digital_twins_client.digital_twins.check_name_availability({"name": instance_name})

    if not availability_result.name_available:
        print(f"ADT instance name {instance_name} is already in use. Try another name.")
        return

    poller = digital_twins_client.digital_twins.begin_create_or_update(
        resource_group_name,
        instance_name,
        {
            "location": resources_location,
            "tags": {"creator": "babylon"}
        },
    )

    # Long-running operations return a poller object; calling poller.result()
    # waits for completion.
    adt_creation_result = poller.result()
    logger.info(f"Provisioned digital twins instance {adt_creation_result.name}")

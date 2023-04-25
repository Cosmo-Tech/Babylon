import logging
import uuid

from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient

from click import argument
from click import command

from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator
from .....utils.response import CommandResponse
from .....utils.clients import (
    pass_adt_management_client,
    get_azure_credentials,
)
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_adt_management_client
@argument("adt_instance_name", type=QueryType())
@require_platform_key("resource_group_name")
@require_platform_key("resources_location")
@require_platform_key("azure_subscription")
@require_platform_key("principal_id")
@timing_decorator
def create(
    adt_management_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    resources_location: str,
    adt_instance_name: str,
    azure_subscription: str,
    principal_id: str,
) -> CommandResponse:
    """Create a new ADT instance in current platform resource group
    and assign a role adt_data_owner"""

    availability_result = (adt_management_client.digital_twins.check_name_availability(
        digital_twins_instance_check_name={
            "name": adt_instance_name,
            "type": "Microsoft.DigitalTwins/digitalTwinsInstances",
        },
        location=resources_location,
    ))

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
    logger.info(f"Successfully created digital twins instance {adt_creation_result.name}")

    logger.info(f"Adding role assignment to the created instance {adt_creation_result.name}...")

    # Integrated Azure role
    adt_data_owner_role_id = "bcd981a7-7f74-457b-83e1-cceb9e632ffe"

    scope = ("/subscriptions/" + azure_subscription + "/resourceGroups/" + resource_group_name +
             "/providers/Microsoft.DigitalTwins/digitalTwinsInstances/" + adt_instance_name)

    authorization_client = AuthorizationManagementClient(
        credential=get_azure_credentials(),
        subscription_id=azure_subscription,
    )

    try:
        role_assignment = authorization_client.role_assignments.create(
            scope,
            str(uuid.uuid4()),
            {
                "roleDefinitionId":
                    "/subscriptions/" + azure_subscription + "/providers/Microsoft.Authorization/roleDefinitions/" +
                    adt_data_owner_role_id,
                "principalId":
                    principal_id,
                "principalType":
                    "ServicePrincipal",
            },
        )
    except Exception as e:
        logger.error(f"Failed to assign a new role to ADT instance '{adt_instance_name}': {e}")

    return CommandResponse.success({
        "adt_instance": adt_creation_result.name,
        "role_assignment": role_assignment,
    })

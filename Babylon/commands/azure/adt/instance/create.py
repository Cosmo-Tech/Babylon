import logging
import uuid

from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient

from click import argument, option
from click import command

from .....utils.decorators import require_platform_key
from .....utils.decorators import require_deployment_key
from .....utils.decorators import timing_decorator
from .....utils.response import CommandResponse
from .....utils.environment import Environment
from .....utils.typing import QueryType
from .....utils.clients import (
    pass_adt_management_client,
    get_azure_credentials,
)

logger = logging.getLogger("Babylon")


@command()
@pass_adt_management_client
@argument("adt_instance_name", type=QueryType(), default="")
@require_deployment_key("organization_id")
@require_deployment_key("workspace_key")
@require_platform_key("resource_group_name")
@require_platform_key("resources_location")
@require_platform_key("azure_subscription")
@require_platform_key("babylon_principal_id")
@require_platform_key('csm_object_platform_id')
@option("-s", "--select", "select", is_flag=True, help="Save host name adt in configuration file")
@timing_decorator
def create(
    adt_management_client: AzureDigitalTwinsManagementClient,
    organization_id: str,
    workspace_key: str,
    resource_group_name: str,
    resources_location: str,
    adt_instance_name: str,
    azure_subscription: str,
    babylon_principal_id: str,
    csm_object_platform_id: str,
    select: bool = False
) -> CommandResponse:
    """Create a new ADT instance in current platform resource group
    and assign a role adt_data_owner"""

    if not adt_instance_name:
        adt_instance_name = f"{organization_id.lower()}-{workspace_key.lower()}"
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
    adt_host_name = f"https://{adt_creation_result.host_name}"
    logger.info(f"Successfully created digital twins instance {adt_host_name}")

    logger.info(f"Adding role assignment to the created instance {adt_host_name}...")

    #  Integrated Azure role
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
                    babylon_principal_id,
                "principalType":
                    "ServicePrincipal",
            },
        )
    except Exception as e:
        logger.error(f"Failed to assign a new role to ADT instance '{adt_instance_name}': {e}")

    try:
        role_assignment_platform = authorization_client.role_assignments.create(
            scope,
            str(uuid.uuid4()),
            {
                "roleDefinitionId":
                    "/subscriptions/" + azure_subscription + "/providers/Microsoft.Authorization/roleDefinitions/" +
                    adt_data_owner_role_id,
                "principalId":
                    csm_object_platform_id,
                "principalType":
                    "ServicePrincipal",
            },
        )
    except Exception as e:
        logger.error(f"Failed to assign a new role to ADT instance '{adt_instance_name}': {e}")

    if select:
        logger.info("Updated configuration variable digital_twin_url")
        env = Environment()
        env.configuration.set_deploy_var("digital_twin_url", adt_host_name)

    return CommandResponse.success({
        "adt_instance": adt_creation_result.name,
        "role_assignment": role_assignment,
        "role_assignment": role_assignment_platform
    })

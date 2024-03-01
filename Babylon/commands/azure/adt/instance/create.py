import logging
import uuid

from click import command
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, injectcontext
=======
from click import Context, option, pass_context
from click import command
from Babylon.utils.decorators import inject_context_with_resource, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import (
    pass_adt_management_client,
    get_azure_credentials,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
<<<<<<< HEAD
=======
@pass_context
>>>>>>> 53b0a6f8 (add injectcontext)
@timing_decorator
@pass_adt_management_client
@retrieve_state
def create(state: dict,
           adt_management_client: AzureDigitalTwinsManagementClient,
           select: bool = False) -> CommandResponse:
    """
    Create a new ADT instance in current platform resource group
    """
    azure_subscription: str = state['services']['azure']['subscription_id']
    workspace_key: str = state['services']['api']['workspace_key']
    organization_id: str = state['services']['api']['organization_id']
    resource_group_name = state['services']['azure']['resource_group_name']
    resource_group_location = state['services']['azure']['location']
    name = f"{organization_id}-{workspace_key}".lower()
    availability_result = (adt_management_client.digital_twins.check_name_availability(
        digital_twins_instance_check_name={
            "name": name,
            "type": "Microsoft.DigitalTwins/digitalTwinsInstances",
        },
        location=resource_group_location,
    ))

    if not availability_result.name_available:
        logger.info(availability_result.message)
        return CommandResponse.fail()

    try:
        poller = adt_management_client.digital_twins.begin_create_or_update(
            resource_group_name,
            name,
            {
                "location": resource_group_location,
                "tags": {
                    "creator": "babylon"
                }
            },
        )
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to create ADT instance '{name}': {error_message[0]}")
        return CommandResponse.fail()

    # Long-running operations return a poller object; calling poller.result()
    # waits for completion.
    adt_creation_result = poller.result()
    adt_host_name = f"https://{adt_creation_result.host_name}"

    logger.info(f"Adding role assignment to the created instance {adt_host_name}...")
    #  Integrated Azure role
    adt_data_owner_role_id = env.azure['roles']['adt_owner']
    scope = ("/subscriptions/" + azure_subscription + "/resourceGroups/" + resource_group_name +
             "/providers/Microsoft.DigitalTwins/digitalTwinsInstances/" + name)
    authorization_client = AuthorizationManagementClient(
        credential=get_azure_credentials(),
        subscription_id=azure_subscription,
    )

    for principal_id in ['babylon', 'platform']:
        try:
            authorization_client.role_assignments.create(
                scope,
                str(uuid.uuid4()),
                {
                    "roleDefinitionId":
                    "/subscriptions/" + azure_subscription + "/providers/Microsoft.Authorization/roleDefinitions/" +
                    adt_data_owner_role_id,
                    "principalId":
                    state['services'][principal_id]['principal_id'],
                    "principalType":
                    "ServicePrincipal",
                },
            )
        except Exception as e:
            logger.error(f"Failed to assign a new role to ADT instance '{name}': {e}")

    logger.info("Successfully created")
    return CommandResponse.success()

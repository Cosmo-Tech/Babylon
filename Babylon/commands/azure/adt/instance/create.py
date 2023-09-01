import logging
import uuid

from typing import Any
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from click import Context, option, pass_context
from click import command
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import (
    pass_adt_management_client,
    get_azure_credentials,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@timing_decorator
@pass_adt_management_client
@option("--select", "select", is_flag=True, default=True, help="Save host name adt in configuration file")
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
    'azure': ['resource_location', 'resource_group_name', 'subscription_id'],
    'babylon': ['principal_id'],
    'platform': ['principal_id']
})
def create(ctx: Context,
           context: Any,
           adt_management_client: AzureDigitalTwinsManagementClient,
           select: bool = False) -> CommandResponse:
    """
    Create a new ADT instance in current platform resource group
    """
    azure_subscription: str = context['azure_subscription_id']
    name = f"{context['api_organization_id'].lower()}-{context['api_workspace_key'].lower()}"
    availability_result = (adt_management_client.digital_twins.check_name_availability(
        digital_twins_instance_check_name={
            "name": name,
            "type": "Microsoft.DigitalTwins/digitalTwinsInstances",
        },
        location=context['azure_resource_location'],
    ))

    if not availability_result.name_available:
        logger.info(availability_result.message)
        return CommandResponse.fail()

    try:
        poller = adt_management_client.digital_twins.begin_create_or_update(
            context['azure_resource_group_name'],
            name,
            {
                "location": context['azure_resource_location'],
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
    scope = ("/subscriptions/" + azure_subscription + "/resourceGroups/" + context['azure_resource_group_name'] +
             "/providers/Microsoft.DigitalTwins/digitalTwinsInstances/" + name)
    authorization_client = AuthorizationManagementClient(
        credential=get_azure_credentials(),
        subscription_id=azure_subscription,
    )

    for principal_id in ['babylon_principal_id', 'platform_principal_id']:
        try:
            authorization_client.role_assignments.create(
                scope,
                str(uuid.uuid4()),
                {
                    "roleDefinitionId":
                    "/subscriptions/" + azure_subscription + "/providers/Microsoft.Authorization/roleDefinitions/" +
                    adt_data_owner_role_id,
                    "principalId":
                    context[principal_id],
                    "principalType":
                    "ServicePrincipal",
                },
            )
        except Exception as e:
            logger.error(f"Failed to assign a new role to ADT instance '{name}': {e}")

    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="digital_twin_url",
                                  var_value=adt_host_name)
        logger.info(SUCCESS_CONFIG_UPDATED("adt", "digital_twin_url"))
    logger.info("Successfully created")
    return CommandResponse.success()

from logging import getLogger
from typing import Any
from azure.identity import DefaultAzureCredential
from azure.mgmt.eventhub import EventHubManagementClient
from azure.mgmt.eventhub.models import AuthorizationRule
from click import command
from Babylon.utils.decorators import inject_context_with_resource, timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command(name="create-key")
@wrapcontext()
@timing_decorator
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
    'azure': ['resource_group_name', "subscription_id"]
})
def create_key(context: Any) -> CommandResponse:
    """
    Create a new Event Hub key
    """
    azure_subscription = context['azure_subscription_id']
    client = EventHubManagementClient(credential=DefaultAzureCredential(), subscription_id=azure_subscription)
    sas = client.namespaces.create_or_update_authorization_rule(
        resource_group_name=context['azure_resource_group_name'],
        authorization_rule_name="cosmosas",
        namespace_name=f"{context['api_organization_id'].lower()}-{context['api_workspace_key'].lower()}",
        parameters=AuthorizationRule(rights=["Manage", "Listen", "Send"]))
    if sas is None:
        return CommandResponse.fail()
    logger.info("Key successfully created")
    return CommandResponse.success()

from logging import getLogger
from typing import Any
from click import command
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@pass_azure_token("csm_api")
@inject_context_with_resource({"api": ['url', 'organization_id', 'workspace_key', 'workspace_id']})
def send_key(
    context: Any,
    azure_token: str,
) -> CommandResponse:
    """
    Send Event Hub key to given workspace
    """
    org_id = context['api_organization_id']
    work_key = context['api_workspace_key']
    work_id = context['api_workspace_id']
    secret_eventhub = env.get_project_secret(organization_id=org_id, workspace_key=work_key, name="eventhub")
    details_json = {"dedicatedEventHubKey": secret_eventhub.replace("\"", "")}
    response = oauth_request(
        f"{context['api_url']}/organizations/{org_id}/workspaces/{work_id}/secret",
        azure_token,
        type="POST",
        data=details_json)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully update key in workspace {work_id}")
    return CommandResponse.success()

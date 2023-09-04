import logging

from typing import Any, Optional
from click import command
from click import option
from hvac import Client
from Babylon.utils.checkers import check_alphanum
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_azure_token("graph")
@option("--name", "password_name", type=QueryType(), help="Password display name")
@option("--object-id", "object_id", type=QueryType())
@pass_hvac_client
@inject_context_with_resource({'api': ['organization_id', 'workspace_key'], 'app': ['object_id', 'name']})
def create(
    context: Any,
    hvac_client: Client,
    azure_token: str,
    object_id: str,
    password_name: Optional[str] = None,
) -> CommandResponse:
    """
    Register a password or secret to an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-addpassword
    """
    check_alphanum(password_name)
    object_id = object_id or context['app_object_id']
    org_id: str = context['api_organization_id']
    work_key: str = context['api_workspace_key']
    route = f"https://graph.microsoft.com/v1.0/applications/{object_id}/addPassword"
    password_name = password_name or f"secret_{work_key}"
    details = {"passwordCredential": {"displayName": password_name}}
    response = oauth_request(route, azure_token, type="POST", json=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    d = dict(secret=output_data['secretText'])
    prefix = f'{env.organization_name}/{env.tenant_id}/projects/{env.context_id}'
    schema = f'{prefix}/{env.environ_id}/{org_id.lower()}/{work_key.lower()}/{password_name.lower()}'
    hvac_client.write(path=schema, **d)
    logger.info("Successfully created")
    return CommandResponse.success(output_data, verbose=True)

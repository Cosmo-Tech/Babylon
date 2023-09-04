from logging import getLogger
from typing import Any
from click import command
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@inject_context_with_resource({"api": ['url', 'organization_id']})
def get(context: Any, azure_token: str) -> CommandResponse:
    """
    Update organization users RBAC access
    """
    api_url = context['api_url']
    org_id = context['api_organization_id']
    response = oauth_request(f"{api_url}/organizations/{org_id}/security", azure_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    return CommandResponse.success(organization, verbose=True)

import jmespath
from logging import getLogger
from typing import Any, Optional
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({"api": ['url', 'organization_id']})
def get_all(context: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all workspaces details
    """
    logger.info(f"Getting all workspaces from organization {context['api_organization_id']}")
    response = oauth_request(f"{context['api_url']}/organizations/{context['api_organization_id']}/workspaces",
                             azure_token)
    if response is None:
        return CommandResponse.fail()
    workspaces = response.json()
    if filter:
        workspaces = jmespath.search(filter, workspaces)
    return CommandResponse.success(workspaces, verbose=True)

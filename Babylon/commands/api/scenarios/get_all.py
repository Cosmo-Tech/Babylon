from click import command

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import get_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse


@command()
@wrapcontext()
@timing_decorator
def get_all() -> CommandResponse:
    """
    Get all scenarios in the workspace
    """
    token = get_azure_token("csm_api")
    state = {
        "api_url": "https://dev.api.cosmotech.com",
        "organizationId": "o-3z188zr63xk",
        "workspaceId": "w-k91e49pgyw6",
        "azure_token": token,
    }
    service = ScenarioService(state=state)
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)


# import jmespath
#
# from logging import getLogger
# from typing import Any, Optional
# from click import command
# from click import option
# from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
# from Babylon.utils.decorators import timing_decorator
# from Babylon.utils.response import CommandResponse
# from Babylon.utils.decorators import output_to_file
# from Babylon.utils.credentials import pass_azure_token
# from Babylon.utils.request import oauth_request
# from Babylon.utils.environment import Environment
#
# logger = getLogger("Babylon")
# env = Environment()
#
#
# @command()
# @wrapcontext()
# @timing_decorator
# @output_to_file
# @pass_azure_token("csm_api")
# @option("--filter", "filter", help="Filter response with a jmespath query")
# @inject_context_with_resource({"api": ['url', 'organization_id', 'workspace_id']})
# def get_all(context: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
#     """
#     Get all scenarios from the organization
#     """
#     work_id = context['api_workspace_id']
#     logger.info(f"Getting all scenarios from organization: {context['api_organization_id']}, {work_id}")
#     response = oauth_request(
#         f"{context['api_url']}/organizations/{context['api_organization_id']}/workspaces/{work_id}/scenarios",
#         azure_token)
#     if response is None:
#         return CommandResponse.fail()
#     scenarios = response.json()
#     if len(scenarios) and filter:
#         scenarios = jmespath.search(filter, scenarios)
#     return CommandResponse.success(scenarios, verbose=True)

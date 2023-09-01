from logging import getLogger
from typing import Any
from click import command
from click import option
from click import argument
from Babylon.utils.decorators import inject_context_with_resource, timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--org-id", "org_id", type=QueryType(), help="Organization id or referenced in configuration")
@option("--sol-id", "sol_id", type=QueryType(), help="Solution id or referenced in configuration")
@option("--run-template", "run_template_id", help="The run Template identifier", required=True, type=QueryType())
@argument("handler_id", type=QueryType())
@inject_context_with_resource({'api': ['url', 'organization_id', "solution_id"]})
def download(context: Any, azure_token: str, org_id: str, sol_id: str, handler_id: str,
             run_template_id: str) -> CommandResponse:
    """Download a solution handler zip from the solution"""
    organization_id = org_id or context['api_organization_id'],
    solution_id = sol_id or context['api_solution_id']
    response = oauth_request(
        f"{context['api_url']}/organizations/{organization_id}/solutions/{solution_id}"
        f"/runtemplates/{run_template_id}/handlers/{handler_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    logger.info("Successfully downloaded solution handler")
    return CommandResponse.success()

from logging import getLogger
import pathlib

from click import command
from click import option
from click import argument

from .....utils.decorators import require_deployment_key
from .....utils.decorators import timing_decorator
from .....utils.response import CommandResponse
from .....utils.decorators import require_platform_key
from .....utils.credentials import pass_azure_token
from .....utils.request import oauth_request
from .....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@require_deployment_key("organization_id")
@option("-s", "--solution", "solution_id", type=QueryType(), default="%deploy%solution_id")
@argument("handler_id", type=QueryType())
@option("-r", "--run-template", "run_template_id", help="The run Template identifier", required=True, type=QueryType())
@option("-o", "--override", "override", is_flag=True)
def upload(api_url: str, azure_token: str, organization_id: str, solution_id: str, handler_id: str,
           run_template_id: str) -> CommandResponse:
    """Upload a solution handler zip to the solution"""
    response = oauth_request(
        f"{api_url}/organizations/{organization_id}/solutions/{solution_id}"
        "/runtemplates/{run_template_id}/handlers/{handler_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    output_path = pathlib.Path(f"{run_template_id}.zip")
    return CommandResponse.success({"file": str(output_path)})

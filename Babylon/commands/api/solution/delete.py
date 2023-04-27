from logging import getLogger

from click import argument
from click import command
from click import option

from ....utils.credentials import pass_azure_token
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.interactive import confirm_deletion
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@argument("solution_id", type=QueryType(), required=False)
@option("--current", "current", type=QueryType(), is_flag=True, help="Delete solution referenced in configuration")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(api_url: str,
           azure_token: str,
           organization_id: str,
           solution_id: str,
           force_validation: bool = False,
           current: bool = False) -> CommandResponse:
    """Delete a solution from the organization"""
    if current:
        env = Environment()
        solution_id = env.configuration.get_deploy_var("solution_id")

    if not force_validation and not confirm_deletion("solution", solution_id):
        return CommandResponse.fail()

    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions/{solution_id}",
                             azure_token,
                             type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted solution {solution_id} from organization {organization_id}")
    return CommandResponse.success()

from logging import getLogger

from click import command
from click import argument
from click import option

from ....utils.interactive import confirm_deletion
from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request
from ....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@require_deployment_key("organization_id", "organization_id")
@argument("dataset_id", type=QueryType())
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
           dataset_id: str,
           force_validation: bool = False) -> CommandResponse:
    """Delete a dataset from the organization"""
    if not force_validation and not confirm_deletion("dataset", dataset_id):
        return CommandResponse.fail()
    response = oauth_request(f"{api_url}/organizations/{organization_id}/datasets/{dataset_id}",
                             azure_token,
                             type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted dataset {dataset_id} from organization {organization_id}")
    return CommandResponse.success()

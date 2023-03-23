from logging import getLogger

from click import command
from click import argument
from rich.pretty import pprint

from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
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
@output_to_file
def get(api_url: str, azure_token: str, organization_id: str, dataset_id: str) -> CommandResponse:
    """Get all datasets from the organization"""
    response = oauth_request(f"{api_url}/organizations/{organization_id}/datasets/{dataset_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    pprint(dataset)
    return CommandResponse.success(dataset)

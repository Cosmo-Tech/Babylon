from logging import getLogger

from click import command
from click import argument
from click import option

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
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@argument("dataset_tag", type=QueryType())
@output_to_file
def search(api_url: str, azure_token: str, organization_id: str, dataset_tag: str) -> CommandResponse:
    """Get dataset with the given tag from the organization"""
    details = {"datasetTags": [dataset_tag]}
    response = oauth_request(f"{api_url}/organizations/{organization_id}/datasets/search",
                             azure_token,
                             type="POST",
                             json=details)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset, verbose=True)

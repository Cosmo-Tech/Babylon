from logging import getLogger

from click import argument
from click import command

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("organization_id", type=QueryType(), default="%deploy%organization_id")
@output_to_file
def get(api_url: str, azure_token: str, organization_id: str) -> CommandResponse:
    """Get an organization details from the API."""
    response = oauth_request(f"{api_url}/organizations/{organization_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    return CommandResponse.success(organizations, verbose=True)

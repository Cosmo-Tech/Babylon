from logging import getLogger
from typing import Any
from click import command
from click import argument
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@argument("id", type=QueryType())
@inject_context_with_resource({"api": ['url', 'organization_id']})
def get(
    context: Any,
    azure_token: str,
    id: str,
) -> CommandResponse:
    """Get a dataset"""
    org_id = context['api_organization_id']
    response = oauth_request(f"{context['api_url']}/organizations/{org_id}/datasets/{id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset, verbose=True)

from logging import getLogger
from typing import Any
from click import command
from click import argument
from Babylon.utils.decorators import inject_context_with_resource, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@pass_azure_token("csm_api")
@argument("tag", type=QueryType())
@output_to_file
@inject_context_with_resource({"api": ['url', 'organization_id']})
def search(context: Any, azure_token: str, tag: str) -> CommandResponse:
    """Get dataset with the given tag from the organization"""
    details = {"datasetTags": [tag]}
    org_id = context['api_organization_id']
    response = oauth_request(f"{context['api_url']}/organizations/{org_id}/datasets/search",
                             azure_token,
                             type="POST",
                             json=details)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset, verbose=True)

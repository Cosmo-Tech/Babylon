import jmespath

from logging import getLogger
from typing import Any, Optional
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.services.organizations_service import OrganizationsService

logger = getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({"api": ['url']})
def get_all(context: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all organization details
    """
    organizations_service = OrganizationsService(context, azure_token)
    response = organizations_service.get_all()
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    if len(organizations) and filter:
        organizations = jmespath.search(filter, organizations)
    return CommandResponse.success(organizations, verbose=True)

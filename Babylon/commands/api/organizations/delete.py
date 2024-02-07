from logging import getLogger
from typing import Any
from click import Context, argument, command, pass_context
from click import option

from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType
from Babylon.services.organizations_service import OrganizationsService

logger = getLogger("Babylon")


@command()
@wrapcontext()
@pass_context
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("id", type=QueryType(), required=False)
@inject_context_with_resource({"api": ['url', 'organization_id']}, required=False)
def delete(ctx: Context, context: Any, azure_token: str, id: str, force_validation: bool = False) -> CommandResponse:
    """Delete an organization"""

    organizations_service = OrganizationsService(context, azure_token)
    response = organizations_service.delete(ctx, id, force_validation)

    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("organization", response.json()['organization_id']))
    return CommandResponse.success()

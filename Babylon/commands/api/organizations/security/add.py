import json

from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.utils.checkers import check_email
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS__RBAC_UPDATED
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--role", "role", type=QueryType(), required=True, default="viewer")
@option("--email", "email", type=QueryType(), required=True)
@inject_context_with_resource({"api": ['url', 'organization_id']})
def add(context: Any, azure_token: str, role: str, email: str, org_id: str = None) -> CommandResponse:
    """
    Add organization users RBAC access
    """
    check_email(email)
    api_url = context['api_url']
    org_id = context['api_organization_id']

    details = json.dumps({"id": email, "role": role})
    response = oauth_request(f"{api_url}/organizations/{org_id}/security/access",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS__RBAC_UPDATED(org_id))
    return CommandResponse.success(details, verbose=True)

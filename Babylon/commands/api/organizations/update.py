import json
from logging import getLogger
import pathlib
from typing import Any, Optional
from click import Path, argument, command
from click import option
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.messages import SUCCESS_UPDATED
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--file",
        "organization_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom organization description file (yaml or json)")
@argument("id", type=QueryType())
@inject_context_with_resource({"api": ['url', 'organization_id']})
def update(context: Any, azure_token: str, id: str, organization_file: Optional[pathlib.Path]) -> CommandResponse:
    """
    Update an organization
    """
    org_id = id or context['api_organization_id']
    path_file = f"{env.context_id}.{env.environ_id}.organization.yaml"
    organization_file = organization_file or env.working_dir.payload_path / path_file
    if not organization_file.exists():
        return CommandResponse.fail()
    details = env.fill_template(organization_file)
    details = json.loads(details)
    if not details.get('id') == id:
        logger.error(f"{id} not found")
        return CommandResponse.fail()
    response = oauth_request(f"{context['api_url']}/organizations/{org_id}", azure_token, type="PATCH", data=details)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(SUCCESS_UPDATED("organization", org_id))
    return CommandResponse.success(organization, verbose=True)

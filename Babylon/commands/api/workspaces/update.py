import json
from logging import getLogger
import pathlib
from typing import Any
from click import Path, argument
from click import command
from click import option
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--org-id", "org_id", type=QueryType(), help="Organization Id Cosmotech Platform")
@option("--file",
        "workspace_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom workspace description file yaml")
@argument("id", type=QueryType())
@inject_context_with_resource({"api": ['url', 'organization_id', 'workspace_id']})
def update(
    context: Any,
    org_id: str,
    id: str,
    workspace_file: pathlib.Path,
    azure_token: str,
) -> CommandResponse:
    """
    Update a workspace
    """
    organization_id = org_id or context['api_organization_id']
    workspace_id = id or context['api_workspace_id']

    path_file = f"{env.context_id}.{env.environ_id}.workspace.yaml"
    workspace_file = workspace_file or env.working_dir.payload_path / path_file
    if not workspace_file.exists():
        logger.info("qsdqsd")
        return CommandResponse.fail()
    details = env.fill_template(workspace_file)
    response = oauth_request(f"{context['api_url']}/organizations/{organization_id}/workspaces/{workspace_id}",
                             azure_token,
                             type="PATCH",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    logger.info(f"Successfully updated workspace {workspace['id']}")
    return CommandResponse.success(workspace, verbose=True)

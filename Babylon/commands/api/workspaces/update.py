import pathlib

from logging import getLogger
from typing import Any, Optional
from click import Path, argument
from click import command
from click import option
from Babylon.utils.checkers import check_ascii, check_email
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
@option("--organization-id", "org_id", type=QueryType(), help="Organization Id Cosmotech Platform")
@option("--file",
        "workspace_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom workspace description file yaml")
@option("--email", "security_id", help="Workspace security_id aka email")
@option("--role", "security_role", required=True, default="admin", help="Workspace security role")
@argument("id", type=QueryType())
@inject_context_with_resource({
    "azure": ['email'],
    "api": ['url', 'organization_id', 'workspace_key', 'workspace_id']
})
def update(context: Any,
           azure_token: str,
           org_id: str,
           id: str,
           workspace_file: pathlib.Path,
           security_id: Optional[str] = None,
           security_role: Optional[str] = None) -> CommandResponse:
    """
    Update a workspace
    """
    security_id = security_id or context['azure_email']
    check_email(security_id)
    organization_id = org_id or context['api_organization_id']
    workspace_id = id or context['api_workspace_id']
    work_key = context['api_workspace_key']
    path_file = f"{env.context_id}.{env.environ_id}.workspace.yaml"
    workspace_file = workspace_file or env.working_dir.payload_path / path_file
    if not workspace_file.exists():
        logger.info("File not found")
        return CommandResponse.fail()
    azf_secret = env.get_project_secret(organization_id=context['api_organization_id'].lower(),
                                        workspace_key=work_key,
                                        name="func")
    details = env.fill_template(workspace_file,
                                data={
                                    "functionUrl":
                                    f"{context['api_organization_id'].lower()}-{context['api_workspace_key'].lower()}",
                                    "key": context['api_workspace_key'],
                                    "security_id": security_id.lower(),
                                    "azf_key": azf_secret,
                                    "security_role": security_role.lower()
                                })
    response = oauth_request(f"{context['api_url']}/organizations/{organization_id}/workspaces/{workspace_id}",
                             azure_token,
                             type="PATCH",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    logger.info(f"Successfully updated workspace {workspace['id']}")
    return CommandResponse.success(workspace, verbose=True)

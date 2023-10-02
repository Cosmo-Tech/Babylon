import pathlib

from logging import getLogger
from posixpath import basename
import sys
from typing import Any, Optional
from click import Context, argument, pass_context
from click import command
from click import option
from click import Path
from Babylon.utils.checkers import check_ascii, check_email
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED, SUCCESS_UPDATED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--file",
        "w_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom workspace description file (yaml or json)")
@option("--email", "security_id", help="Workspace security_id aka email")
@option("--role", "security_role", required=True, default="admin", help="Workspace security role")
@option("--select", "select", is_flag=True, default=True, help="Save this new workspace in configuration")
@argument("name", type=QueryType())
@inject_context_with_resource({
    "azure": ['email'],
    "api": ['url', 'organization_id', 'workspace_key', 'solution_id', 'run_templates'],
    "powerbi": ['dashboard_view', 'scenario_view']
})
def create(ctx: Context,
           context: Any,
           azure_token: str,
           name: str,
           w_file: Optional[pathlib.Path] = None,
           security_id: Optional[str] = None,
           security_role: Optional[str] = None,
           select: bool = False) -> CommandResponse:
    """
    Register a workspace.
    """
    check_ascii(name)
    security_id = security_id or context['azure_email']
    check_email(security_id)
    work_key = context['api_workspace_key']
    path_file = f"{env.context_id}.{env.environ_id}.workspace.yaml"
    t_file = w_file or env.working_dir.payload_path / path_file
    if not t_file.exists():
        logger.error(f"No such file: '{basename(t_file)}' in .payload directory")
        sys.exit(1)
    azf_secret = env.get_project_secret(organization_id=context['api_organization_id'].lower(),
                                        workspace_key=work_key,
                                        name="func")
    details = env.fill_template(t_file,
                                data={
                                    "functionUrl":
                                    f"{context['api_organization_id'].lower()}-{context['api_workspace_key'].lower()}",
                                    "name": name,
                                    "key": context['api_workspace_key'],
                                    "security_id": security_id.lower(),
                                    "azf_key": azf_secret,
                                    "security_role": security_role.lower()
                                })
    response = oauth_request(f"{context['api_url']}/organizations/{context['api_organization_id']}/workspaces",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="workspace_id",
                                  var_value=workspace["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("api", "workspace_id"))
    logger.info(SUCCESS_UPDATED("workspace", workspace["id"]))
    return CommandResponse.success(workspace, verbose=True)

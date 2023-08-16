import pathlib

from logging import getLogger
from posixpath import basename
import sys
from typing import Any, Optional
from click import Context, argument, pass_context
from click import command
from click import option
from click import Path
from Babylon.utils.checkers import check_alphanum, check_email
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED, SUCCESS_CREATED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_context
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--email", "security_id", type=QueryType(), help="Email valid")
@option("--role", "security_role", type=QueryType(), default="Admin", required=True, help="Role RBAC")
@option("--file",
        "org_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom organization description file (yaml or json)")
@option("--select", "select", is_flag=True, default=True, help="Save this new organization in configuration")
@argument("name", type=QueryType())
@inject_context_with_resource({"api": ['url'], "azure": ['email']}, required=False)
def create(
    ctx: Context,
    context: Any,
    azure_token: str,
    name: str,
    security_id: str,
    security_role: str,
    select: bool,
    org_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Register new orgnanization
    """
    check_alphanum(name)
    security_id = security_id or context['azure_email']
    check_email(security_id)

    path_file = f"{env.context_id}.{env.environ_id}.organization.yaml"
    org_file = org_file or env.working_dir.payload_path / path_file
    if not org_file.exists():
        logger.error(f"No such file: '{basename(org_file)}' in .payload directory")
        sys.exit(1)

    details = env.fill_template(org_file,
                                data={
                                    "name": name,
                                    "security_id": security_id,
                                    "security_role": security_role
                                })
    response = oauth_request(f"{context['api_url']}/organizations", azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="organization_id",
                                  var_value=organization["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("organizations", organization["id"]))
    logger.info(SUCCESS_CREATED("organizations", organization["id"]))
    return CommandResponse.success(organization, verbose=True)

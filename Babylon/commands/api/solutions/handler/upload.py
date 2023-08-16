import pathlib
from logging import getLogger

from typing import Any
from click import command
from click import option
from click import argument
from click import Path
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option(
    "--run-template",
    "run_template_id",
    help="The run Template identifier name example: 'Sensitive analysis'",
    type=QueryType(),
    required=True,
)
@option("--override", "override", is_flag=True, help="Override handler solution")
@argument("handler_id", type=QueryType())
@argument("handler_path", type=Path(path_type=pathlib.Path, exists=True))
@inject_context_with_resource({'api': ['url', 'organization_id', "solution_id"]})
def upload(context: Any,
           azure_token: str,
           handler_path: pathlib.Path,
           handler_id: str,
           run_template_id: str,
           override: bool = False) -> CommandResponse:
    """Upload a solution handler zip to the solution"""
    org_api = context['api_organization_id']
    if not handler_path.endswith(".zip"):
        logger.error("solution handler upload only supports zip files")
        return CommandResponse.fail()
    with open(handler_path, "rb") as handler:
        response = oauth_request(
            f"{context['api_url']}/organizations/{org_api}/solutions/{context['api_solution_id']}"
            f"/runtemplates/{run_template_id}/handlers/{handler_id}",
            azure_token,
            files={handler_path.name: handler},
            params={"overwrite": override},
            headers={"Content-Type": "application/octet-stream"},
            type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully sent handler file {handler_path} to solution {context['api_solution_id']}")
    return CommandResponse.success()

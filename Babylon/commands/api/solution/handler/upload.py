from logging import getLogger
import pathlib

from click import command
from click import option
from click import argument
from click import Path

from .....utils.decorators import timing_decorator
from .....utils.response import CommandResponse
from .....utils.decorators import require_platform_key
from .....utils.credentials import pass_azure_token
from .....utils.request import oauth_request
from .....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--solution", "solution_id", type=QueryType(), default="%deploy%solution_id")
@argument("handler_path", type=Path(path_type=pathlib.Path, exists=True))
@argument("handler_id", type=QueryType())
@option(
    "-r",
    "--run-template",
    "run_template_id",
    help="The run Template identifier",
    type=QueryType(),
    required=True,
)
@option("-o", "--override", "override", is_flag=True)
def upload(api_url: str,
           azure_token: str,
           organization_id: str,
           solution_id: str,
           handler_path: pathlib.Path,
           handler_id: str,
           run_template_id: str,
           override: bool = False) -> CommandResponse:
    """Upload a solution handler zip to the solution"""
    if not handler_path.endswith(".zip"):
        logger.error("solution handler upload only supports zip files")
        return CommandResponse.fail()
    with open(handler_path, "rb") as handler:
        response = oauth_request(
            f"{api_url}/organizations/{organization_id}/solutions/{solution_id}"
            f"/runtemplates/{run_template_id}/handlers/{handler_id}",
            azure_token,
            files={handler_path.name: handler},
            params={"overwrite": override},
            headers={"Content-Type": "application/octet-stream"},
            type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully sent handler file {handler_path} to solution {solution_id}")
    return CommandResponse.success()

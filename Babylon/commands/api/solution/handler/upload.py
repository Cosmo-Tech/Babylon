import pathlib
from logging import getLogger

from click import Choice
from click import Path
from click import argument
from click import command
from click import option

from .....utils.credentials import pass_azure_token
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator
from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--solution", "solution_id", type=QueryType(), default="%deploy%solution_id")
@argument(
    "handler_path",
    type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
)
@argument(
    "handler_id",
    type=Choice([
        "parameters_handler",
        "validator",
        "prerun",
        "engine",
        "postrun",
        "scenariosdata_transform",
    ]),
)
@option(
    "-r",
    "--run-template",
    "run_template_id",
    help="The run Template identifier name example: 'Sensitive analysis'",
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
    if not handler_path.name.endswith(".zip"):
        logger.error("solution handler upload only supports zip files")
        return CommandResponse.fail()
    handler = open(handler_path, "rb")
    response = oauth_request(
        f"{api_url}/organizations/{organization_id}/solutions/{solution_id}"
        f"/runtemplates/{run_template_id}/handlers/{handler_id}/upload",
        azure_token,
        data=handler.read(),
        params={"overwrite": override},
        headers={"Content-Type": "application/octet-stream"},
        type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully sent handler file {handler_path} to solution {solution_id}")
    return CommandResponse.success()

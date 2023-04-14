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
    help="The run Template identifier name exaple: 'Sensitive analysis'",
    type=QueryType(),
    required=True,
)
@option("-o", "--output", "output_folder", help="Output folder", type=Path(path_type=pathlib.Path))
def download(api_url: str, azure_token: str, organization_id: str, solution_id: str, handler_id: str,
             run_template_id: str, output_folder: pathlib.Path) -> CommandResponse:
    """Download a solution handler zip from the solution"""
    response = oauth_request(
        f"{api_url}/organizations/{organization_id}/solutions/{solution_id}"
        f"/runtemplates/{run_template_id}/handlers/{handler_id}/download", azure_token)
    if response is None:
        return CommandResponse.fail()
    output_path = pathlib.Path(f"{run_template_id}.zip")
    if output_folder:
        output_path = output_folder / output_path
    with open(output_path, "wb") as _f:
        _f.write(response.read())
    logger.info(f"Successfully downloaded solution handler to {output_path}")
    return CommandResponse.success({"file": str(output_path)})

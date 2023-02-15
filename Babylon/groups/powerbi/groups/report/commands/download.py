import logging
from typing import Optional
import pathlib

from click import command
from click import argument
from click import option
from click import Path

from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("report_id")
@option("-o",
        "--output_file",
        "output_file",
        type=Path(writable=True, dir_okay=False, path_type=pathlib.Path),
        required=True,
        help="output filename (.pbix)")
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def download(powerbi_workspace_id: str,
             report_id: str,
             output_file: str,
             workspace_id: Optional[str] = None) -> CommandResponse:
    """Download a report in the current workspace"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    output_file = output_file if output_file.suffix == ".pbix" else f"{output_file}.pbix"
    url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
    logger.info(f"Downloading report {report_id} in file {output_file}...")
    response = oauth_request(url_report, get_azure_token("powerbi"))
    if response is None:
        return CommandResponse.fail()
    with open(output_file, "wb") as file:
        file.write(response.content)
        logger.info(f"Report was saved as {output_file}")
    return CommandResponse.success({"file": output_file})

import logging
import pathlib
from typing import Optional

from click import command
from click import argument
from click import option
from click import Path

from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.credentials import pass_azure_token
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@argument("report_id", type=QueryType())
@option("-o", "--output", "output_folder", help="Output folder", type=Path(path_type=Patth(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)), default="POWERBI")
@option("-w",
        "--workspace",
        "workspace_id",
        help="PowerBI workspace ID",
        type=QueryType(),
        default="%deploy%powerbi_workspace_id")
def download(azure_token: str, report_id: str, workspace_id: str,
             output_folder: Optional[pathlib.Path]) -> CommandResponse:
    """Download a report in the current workspace"""
    url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
    response = oauth_request(url_report, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_path = pathlib.Path(response.headers.get("X-PowerBI-FileName"))
    if output_folder:
        output_path = output_folder / output_path
    with open(output_path, "wb") as file:
        file.write(response.content)
    logger.info(f"Report {report_id} was saved as {output_path}")
    return CommandResponse.success({"file": output_path})

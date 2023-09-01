import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import option
from click import Path
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_powerbi_token()
@option("-o", "--output", "output_folder", type=Path(path_type=pathlib.Path), default="powerbi", help="Output folder")
@option("--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("report_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def download(context: Any, powerbi_token: str, report_id: str, workspace_id: str,
             output_folder: Optional[pathlib.Path]) -> CommandResponse:
    """
    Download a report in the current workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
    response = oauth_request(url_report, powerbi_token)
    if response is None:
        return CommandResponse.fail()
    output_path = pathlib.Path(response.headers.get("X-PowerBI-FileName"))
    if output_folder:
        output_path = output_folder / output_path
    with open(output_path, "wb") as file:
        file.write(response.content)
    logger.info(f"Report {report_id} was saved as {output_path}")
    return CommandResponse.success({"file": output_path})

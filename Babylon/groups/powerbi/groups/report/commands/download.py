import logging
import requests
from typing import Optional
import pathlib

from click import command
from click import pass_context
from click import Context
from click import argument
from click import option
from click import Path

from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("report_id")
@option("-o",
        "--output_file",
        "output_file",
        type=Path(writable=True, dir_okay=False, path_type=pathlib.Path),
        required=True,
        help="output filename (.pbix)")
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def download(ctx: Context,
             powerbi_workspace_id: str,
             report_id: str,
             output_file: str,
             workspace_id: Optional[str] = None) -> CommandResponse:
    """Download a report"""
    access_token = ctx.obj.token
    workspace_id = workspace_id or powerbi_workspace_id
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
    try:
        response = requests.get(url=url_report, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    with open(output_file, "wb") as file:
        file.write(response.content)
        logger.info(f"Report was saved as {output_file}")
    return CommandResponse(data={"file": output_file})

import logging
from typing import Optional
import pathlib

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import argument
from click import option
from click import Path

from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse
from ......utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id", required=False)
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
    access_token = ctx.find_object(AccessToken).token
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
    response = oauth_request(url=url_report, access_token=access_token)
    if response is None:
        return CommandResponse.fail()
    with open(output_file, "wb") as file:
        file.write(response)
        logger.info(f"Report was saved as {output_file}")
    return CommandResponse(data={"file": output_file})

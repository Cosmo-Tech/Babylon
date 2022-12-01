import logging
import requests

from click import command
from click import pass_context
from click import Context
from click import argument
from click import option
from click import Path

from ......utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("report_id")
@option("-o",
        "--output_file",
        "output_file",
        type=Path(writable=True, dir_okay=False),
        required=True,
        help="output filename (.pbix)")
def download(ctx: Context, powerbi_workspace_id: str, report_id: str, output_file: str):
    """Download a report"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{powerbi_workspace_id}/reports/{report_id}/Export"
    response = requests.get(url=url_report, headers=header)
    with open(output_file, "wb") as file:
        file.write(response.content)

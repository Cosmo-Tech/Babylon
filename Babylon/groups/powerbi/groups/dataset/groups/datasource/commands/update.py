import logging
import requests
import json

from click import command
from click import argument
from click import pass_context
from click import Context
from click import Path

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("report_id")
@argument("update_file", type=Path(readable=True, dir_okay=False))
def update(ctx: Context, report_id: str, update_file: str):
    """Update datasource"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/reports/{report_id}/Default.UpdateDatasources"
    with open(update_file, "r") as _file:
        data = json.load(_file)
    response = requests.post(url=update_url, data=data, headers=header)
    logger.info(response.json())

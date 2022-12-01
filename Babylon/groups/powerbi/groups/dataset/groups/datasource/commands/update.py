import logging
import requests
import json

from click import command
from click import argument
from click import pass_context
from click import Context
from click import Path

from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("dataset_id")
@argument("update_file", type=Path(readable=True, dir_okay=False))
def update(ctx: Context, dataset_id: str, update_file: str) -> CommandResponse:
    """Update datasource"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/Default.UpdateDatasources"
    with open(update_file, "r") as _file:
        data = json.load(_file)
    try:
        response = requests.post(url=update_url, data=data, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(response.json())
    return CommandResponse(data=response.json())

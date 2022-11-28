import logging
import requests

from click import pass_context
from click import Context
from click import command
from click import argument
from click import Path

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("pbxi_file", type=Path(readable=True, dir_okay=False))
def publish(ctx: Context, pbxi_file: str):
    """Publish the given pbxi file to the PowerBI workspace"""
    header = {"Authorization": f"Bearer {ctx.parent.obj}"}
    dataset = "model.json"
    route = f"https://api.powerbi.com/v1.0/myorg/imports?datasetDisplayName={dataset}"
    session = requests.Session()
    with open(pbxi_file, "rb") as _f:
        files = {'file': (pbxi_file, _f)}
        response = session.post(url=route, headers=header, files=files)
    print(response)

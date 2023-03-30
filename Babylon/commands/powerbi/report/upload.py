import logging
import os
import pathlib
import time

import requests
from click import command
from click import argument
from click import Path
from click import option

from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.typing import QueryType
from ....utils.credentials import pass_azure_token
from rich.progress import Progress, SpinnerColumn, TextColumn

logger = logging.getLogger("Babylon")

RETRY_WAIT_TIME = 0.5


@command()
@pass_azure_token("powerbi")
@argument("pbix_filename", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-w",
        "--workspace",
        "workspace_id",
        help="PowerBI workspace ID",
        type=QueryType(),
        default="%deploy%powerbi_workspace_id")
@option("--override", "override", is_flag=True, help="override reports in case of name conflict ?")
@timing_decorator
def upload(azure_token: str, pbix_filename: str, workspace_id: str, override: bool = False) -> CommandResponse:
    """Publish the given pbxi file to the PowerBI workspace"""
    name = os.path.splitext(pbix_filename)[0]
    header = {"Content-Type": "multipart/form-data", "Authorization": f"Bearer {azure_token}"}
    name_conflict = "CreateOrOverwrite" if override else "Abort"
    route = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
             f"/imports?datasetDisplayName={name}&nameConflict={name_conflict}")
    session = requests.Session()
    with open(pbix_filename, "rb") as _f:
        try:
            response = session.post(url=route, headers=header, files={"file": _f})
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return CommandResponse.fail()
        if response.status_code >= 300:
            logger.error(f"Request failed ({response.status_code}): {response.text}")
            return CommandResponse.fail()
    import_data = response.json()
    # Wait for import end
    route = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports/{import_data.get('id')}"
    output_data = {}
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("Waiting for import to finish...")
        while True:
            time.sleep(RETRY_WAIT_TIME)
            response = oauth_request(route, azure_token)
            output_data = response.json()
            if output_data.get("importState") != "Publishing":
                break
    if output_data.get("importState") != "Succeeded":
        logger.error(f"Failed to import report file {pbix_filename}")
        return CommandResponse.fail()
    logger.info(f"Successfully imported report {pbix_filename}")
    return CommandResponse.success(output_data, verbose=True)

import logging
import pprint

from click import command
from click import argument
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_tfc_client
from ....utils.typing import QueryType
from ....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@output_to_file
@argument("workspace_id", type=QueryType(), default="%deploy%terraform_cloud_workspace_id")
@timing_decorator
def last_run(tfc_client: TFC, workspace_id: str) -> CommandResponse:
    """Get state of the last run of a workspace"""
    try:
        r = tfc_client.runs.list_all(workspace_id=workspace_id)['data']
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} has no runs")
        return CommandResponse.fail()

    ordered_runs = sorted(r, key=lambda run: run['attributes']['created-at'])

    logger.info(pprint.pformat(ordered_runs[-1]))

    return CommandResponse.success(r.get("data"))

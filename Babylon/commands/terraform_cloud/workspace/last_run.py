import logging

from click import command
from click import argument
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@output_to_file
@pass_tfc_client
@argument("workspace_id", type=QueryType())
def last_run(tfc_client: TFC, workspace_id: str) -> CommandResponse:
    """
    Get state of the last run of a workspace
    """
    try:
        r = tfc_client.runs.list_all(workspace_id=workspace_id)['data']
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} has no runs")
        return CommandResponse.fail()

    ordered_runs = sorted(r, key=lambda run: run['attributes']['created-at'])

    if not ordered_runs:
        logger.info(f"No runs found in workspace {workspace_id}")
        return CommandResponse.success()

    return CommandResponse.success(ordered_runs[-1].get("data"), verbose=True)

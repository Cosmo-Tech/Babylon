import logging
from typing import Optional

from click import command, option
from click import argument
import jmespath
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
@option("--filter", "filter", help="Filter response with a jmespath query")
@timing_decorator
def last_run(tfc_client: TFC, workspace_id: str, filter: Optional[str] = None) -> CommandResponse:
    """Get state of the last run of a workspace"""
    try:
        r = tfc_client.runs.list_all(workspace_id=workspace_id)['data']
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} has no runs")
        return CommandResponse.fail()

    ordered_runs = sorted(r, key=lambda run: run['attributes']['created-at'])

    if not ordered_runs:
        logger.info(f"No runs found in workspace {workspace_id}")
        return CommandResponse.success()

    run_data = ordered_runs[-1]
    if filter:
        run_data = jmespath.search(filter, run_data)

    return CommandResponse.success(run_data, verbose=True)

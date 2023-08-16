import logging
import webbrowser

from click import argument
from click import command
from click import option
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
@option("--states",
        "states_webpage_open",
        is_flag=True,
        help="Add this option to open the webapp page to the states of the workspace")
@argument("workspace_id", type=QueryType())
def outputs(tfc_client: TFC, workspace_id: str, states_webpage_open: bool) -> CommandResponse:
    """
    List outputs of a workspace
    Sensitive outputs are not readable, use -s option to access the state in the web application to get those
    """
    try:
        ws = tfc_client.workspaces.show(workspace_id=workspace_id)
        ws_name = ws['data']['attributes']['name']
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()

    try:
        ws = tfc_client.state_version_outputs.show_current_for_workspace(workspace_id=workspace_id)
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} has no outputs")
        return CommandResponse.fail()

    state_url = f"{tfc_client.get_url()}/app/{tfc_client.get_org()}/workspaces/{ws_name}/states"
    if states_webpage_open:
        logger.info(f"Opening states URL : {state_url}")
        webbrowser.open(state_url)
    else:
        logger.info(f"Full state info can be found at : {state_url}")
    return CommandResponse.success(ws.get("data"), verbose=True)

import json
import logging
import pathlib
import pprint
import webbrowser
from typing import Optional

import click
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.decorators import working_dir_requires_yaml_key
from ....utils.clients import pass_tfc_client

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="File to which content should be outputted (json-formatted)",
)
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use")
@option("-s",
        "--states",
        "states_webpage_open",
        is_flag=True,
        help="Add this option to open the webapp page to the states of the workspace.\n"
        "(Allow to see content of sensitives outputs)")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@timing_decorator
def outputs(tfc_client: TFC, workspace_id_wd: str, workspace_id: Optional[str], output_file: Optional[pathlib.Path],
            states_webpage_open: bool) -> CommandResponse:
    """List outputs of a workspace.

Sensitive outputs are not readable, use -s option to access the state in the web application to get those."""
    workspace_id = workspace_id or workspace_id_wd
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

    logger.info(pprint.pformat(ws['data']))

    state_url = f"{tfc_client.get_url()}/app/{tfc_client.get_org()}/workspaces/{ws_name}/states"
    if states_webpage_open:
        logger.info(f"Opening states URL : {state_url}")
        webbrowser.open(state_url)
    else:
        logger.info(f"Full state info can be found at : {state_url}")

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(ws['data'], _file, ensure_ascii=False)
    return CommandResponse.success(ws.get("data"))

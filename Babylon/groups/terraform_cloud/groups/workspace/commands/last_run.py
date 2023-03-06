import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

from ......utils.decorators import timing_decorator
from ......utils.decorators import working_dir_requires_yaml_key
from ......utils.response import CommandResponse
from ......utils.clients import pass_tfc_client

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
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@timing_decorator
def last_run(tfc_client: TFC, workspace_id_wd: str, workspace_id: Optional[str],
             output_file: Optional[pathlib.Path]) -> CommandResponse:
    """Get state of the last run of a workspace"""
    workspace_id = workspace_id or workspace_id_wd
    try:
        r = tfc_client.runs.list_all(workspace_id=workspace_id)['data']
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} has no runs")
        return CommandResponse.fail()

    ordered_runs = sorted(r, key=lambda run: run['attributes']['created-at'])

    logger.info(pprint.pformat(ordered_runs[-1]))

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(r['data'], _file, ensure_ascii=False)
    return CommandResponse.success(r.get("data"))

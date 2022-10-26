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

from ......utils.decorators import working_dir_requires_yaml_key

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use")
@option("-o", "--output", "output_file",
        type=click.Path(file_okay=True,
                        dir_okay=False,
                        readable=True,
                        path_type=pathlib.Path),
        help="File to which content should be outputted (json-formatted)", )
def get(api: TFC,
        workspace_id_wd: str,
        workspace_id: Optional[str],
        output_file: Optional[pathlib.Path]):
    """Get a workspace in the organization"""
    workspace_id = workspace_id or workspace_id_wd
    try:
        ws = api.workspaces.show(workspace_id=workspace_id)
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return

    logger.info(pprint.pformat(ws['data']))

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(ws['data'], _file, ensure_ascii=False)

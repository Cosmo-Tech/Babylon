import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from click import command
from click import option
from terrasnek.api import TFC

from ......utils.decorators import timing_decorator
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
@timing_decorator
def get_all(tfc_client: TFC, output_file: Optional[pathlib.Path]) -> CommandResponse:
    """Get all available workspaces in the organization"""
    ws = tfc_client.workspaces.list()
    r = []

    def get_last_changed(_r):
        return _r.get('attributes', {}).get('latest-change-at', '')

    for _ws in sorted(ws.get('data'), key=get_last_changed):
        logger.info(pprint.pformat(_ws))
        r.append(_ws)

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(r, _file, ensure_ascii=False)
    return CommandResponse.success({"workspaces": r})

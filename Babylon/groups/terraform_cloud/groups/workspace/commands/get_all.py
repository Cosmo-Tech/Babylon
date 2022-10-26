import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from click import command
from click import option
from terrasnek.api import TFC

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="File to which content should be outputted (json-formatted)",
)
def get_all(api: TFC, output_file: Optional[pathlib.Path]):
    """Get all available workspaces in the organization"""
    ws = api.workspaces.list()
    r = []

    def get_last_changed(_r):
        return _r.get('attributes', {}).get('latest-change-at', '')

    for _ws in sorted(ws.get('data'), key=get_last_changed):
        logger.info(pprint.pformat(_ws))
        r.append(_ws)

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(r, _file, ensure_ascii=False)

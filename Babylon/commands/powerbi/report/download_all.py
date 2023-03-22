import logging
import pathlib

from click import command
from click import option
from click import Path

from ....utils.response import CommandResponse
from ....utils.macro import Macro
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@option("-w",
        "--workspace",
        "workspace_id",
        help="PowerBI workspace ID",
        type=QueryType(),
        default="%deploy%powerbi_workspace_id")
@option("-o", "--output", "output_folder", help="Output folder", type=Path(path_type=pathlib.Path), default="reports")
def download_all(workspace_id: str, output_folder: pathlib.Path) -> CommandResponse:
    """Download all reports from a workspace"""
    logger.info(f"Downloading reports from workspace {workspace_id}...")
    if not output_folder.exists():
        output_folder.mkdir()
    m = Macro("PowerBI download all") \
        .step(["powerbi", "report", "get-all", "-w", workspace_id], store_at="reports") \
        .iterate("%datastore%reports.data",
                 ["powerbi", "report", "download", "-w", workspace_id, "%datastore%item.id", "-o", str(output_folder) ])
    reports = m.env.get_data(["reports", "data"])
    logger.info(f"Successfully saved the following reports:")
    logger.info("\n".join(f"- {output_folder}/{report['name']}.pbix" for report in reports))
    return CommandResponse.success(m.env.get_data(["reports", "data"]))
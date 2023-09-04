import logging
import pathlib

from typing import Any
from click import command
from click import option
from click import Path
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.macro import Macro
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@option("--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--output", "output_folder", help="Output folder", type=Path(path_type=pathlib.Path), default="powerbi")
@inject_context_with_resource({"powerbi": ['workspace']})
def download_all(context: Any, workspace_id: str, output_folder: pathlib.Path) -> CommandResponse:
    """
    Download all reports from a workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    logger.info(f"Downloading reports from workspace {workspace_id}...")
    if not output_folder.exists():
        output_folder.mkdir()
    m = Macro("PowerBI download all", "powerbi") \
        .step(["powerbi", "report", "get-all", "--workspace", workspace_id], store_at="reports") \
        .iterate("datastore.reports.data",
                 ["powerbi", "report", "download", "--workspace",
                  workspace_id, "%datastore%item.id", "-o", str(output_folder)])
    reports = m.env.get_data(["reports", "data"])
    logger.info("Successfully saved the following reports:")
    logger.info("\n".join(f"- {output_folder}/{report['name']}.pbix" for report in reports))
    return CommandResponse.success(m.env.get_data(["reports", "data"]))

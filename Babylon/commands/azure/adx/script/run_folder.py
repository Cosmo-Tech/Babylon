import glob
import logging
import pathlib

from click import Context, Path, command, pass_context, argument
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.response import CommandResponse
from .run import run

logger = logging.getLogger("Babylon")


@command()
@wrapcontext
@timing_decorator
@pass_context
@pass_kusto_client
@argument("script_folder",
          type=Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=pathlib.Path))
def run_folder(
    ctx: Context,
    kusto_client: KustoManagementClient,
    script_folder: pathlib.Path,
) -> CommandResponse:
    """
    Run all script files (.kql) from SCRIPT_FOLDER
    """
    files = glob.glob(str(script_folder.absolute() / "*.kql"))
    if not files:
        logger.error(f"No script found in path {script_folder.absolute()}")
        return CommandResponse.fail()
    for _file in files[::-1]:
        file_path = pathlib.Path(_file)
        logger.info(f"Found script {file_path} sending it to the database.")
        ctx.invoke(run, script_file=file_path)
    return CommandResponse.success()

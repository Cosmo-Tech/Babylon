import glob
import logging
import pathlib

import click
from azure.mgmt.kusto import KustoManagementClient

from .....utils.decorators import describe_dry_run
from .....utils.decorators import require_deployment_key
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator
from .....utils.clients import pass_kusto_client
from .....utils.response import CommandResponse
from .run import run

logger = logging.getLogger("Babylon")


@click.command()
@click.pass_context
@pass_kusto_client
@require_platform_key("adx_cluster_name")
@require_platform_key("resource_group_name")
@require_deployment_key("adx_database_name")
@click.argument("script_folder",
                type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=pathlib.Path))
@describe_dry_run("Would go through the folder and run all files found")
@timing_decorator
def run_folder(
    ctx: click.Context,
    kusto_client: KustoManagementClient,
    adx_cluster_name: str,
    resource_group_name: str,
    adx_database_name: str,
    script_folder: pathlib.Path,
) -> CommandResponse:
    """Run all script files (.kql) from SCRIPT_FOLDER"""
    files = glob.glob(str(script_folder / "*.kql"))
    if not files:
        logger.error(f"No script found in path {script_folder.absolute()}")
        return CommandResponse.fail()
    for _file in files[::-1]:
        file_path = pathlib.Path(_file)
        logger.info(f"Found script {file_path} sending it to the database.")
        ctx.invoke(run, script_file=file_path)
    return CommandResponse.success()

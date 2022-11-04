import logging
import pathlib
import time

import click
from azure.core.exceptions import HttpResponseError
from azure.mgmt.kusto import KustoManagementClient
from click import make_pass_decorator

from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ......utils.decorators import timing_decorator

pass_kmc = make_pass_decorator(KustoManagementClient)

logger = logging.getLogger("Babylon")


@click.command()
@pass_kmc
@require_platform_key("cluster_name")
@require_platform_key("resource_group_name")
@require_deployment_key("database_name")
@click.argument("script_file",
                type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@describe_dry_run("Would send the content of the given script to ADX then delete it once run is finished")
@timing_decorator
def run_script(kmc: KustoManagementClient, cluster_name: str, resource_group_name: str, database_name: str,
               script_file: pathlib.Path):
    """Open SCRIPT_FILE and run it on the database

In the script instances of "<database name>" will be replaced by the actual database name"""
    if script_file.suffix != ".kql":
        logger.warning(f"File {script_file.name} is not a kql file. Errors could happen.")
    script_name = f"{int(time.time() // 1)}-{script_file.name}"
    with open(script_file) as _script_file:
        logger.info(f"Reading {script_file}")
        script_content = _script_file.read().replace("<database name>", database_name)
        logger.info("Sending script to database.")
        s = kmc.scripts.begin_create_or_update(resource_group_name=resource_group_name,
                                               cluster_name=cluster_name,
                                               database_name=database_name,
                                               script_name=script_name,
                                               parameters={"script_content": script_content},
                                               polling_interval=1)
        try:
            with click.progressbar(length=20, label="Waiting for script to finish") as bar:
                for _ in bar:
                    if not s.done():
                        s.wait(1)
                while not s.done():
                    s.wait(1)
        except HttpResponseError as _resp_error:
            logger.error(_resp_error.message.split("\nMessage:")[1])
        else:
            kmc.scripts.begin_delete(
                resource_group_name=resource_group_name,
                cluster_name=cluster_name,
                database_name=database_name,
                script_name=script_name,
            )
            logger.info("Script successfully ran.")

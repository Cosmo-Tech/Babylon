import logging
import pathlib
import time

from typing import Any
from click import Path, command, argument, progressbar
from azure.core.exceptions import HttpResponseError
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@pass_kusto_client
@argument("script_file", type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def run(context: Any, kusto_client: KustoManagementClient, script_file: pathlib.Path) -> CommandResponse:
    """
    Open SCRIPT_FILE and run it on the database
In the script instances of "<database name>" will be replaced by the actual database name
    """
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']
    database_name = context['adx_database_name']
    if script_file.suffix != ".kql":
        logger.warning(f"File {script_file.name} is not a kql file. Errors could happen.")
    script_name = f"{int(time.time() // 1)}-{script_file.name}"
    with open(script_file) as _script_file:
        logger.info(f"Reading {script_file}")
        script_content = _script_file.read().replace("<database name>", database_name)
        logger.info("Sending script to database.")
        s = kusto_client.scripts.begin_create_or_update(resource_group_name=resource_group_name,
                                                        cluster_name=adx_cluster_name,
                                                        database_name=database_name,
                                                        script_name=script_name,
                                                        parameters={"script_content": script_content},
                                                        polling_interval=1)
        try:
            with progressbar(length=20, label="Waiting for script to finish") as bar:
                for _ in bar:
                    if not s.done():
                        s.wait(1)
                while not s.done():
                    s.wait(1)
        except HttpResponseError as _resp_error:
            logger.error(_resp_error.message.split("\nMessage:")[1])
        else:
            kusto_client.scripts.begin_delete(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                database_name=database_name,
                script_name=script_name,
            )
            logger.info("Successfully ran")
    return CommandResponse.success()

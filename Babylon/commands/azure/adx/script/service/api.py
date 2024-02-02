import time
import glob
import logging

from pathlib import Path
from click import progressbar
from azure.mgmt.kusto import KustoManagementClient
from azure.core.exceptions import HttpResponseError
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


class AdxScriptService:

    def __init__(self) -> None:
        pass

    def get_all(self, context: dict, kusto_client: KustoManagementClient):
        resource_group_name = context["azure_resource_group_name"]
        adx_cluster_name = context["adx_cluster_name"]
        database_name = context["adx_database_name"]
        response = kusto_client.scripts.list_by_database(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=database_name,
        )
        scripts = [item.as_dict() for item in response]
        return scripts

    def run_folder(
        self, context: dict, script_folder: Path, kusto_client: KustoManagementClient
    ):
        files = glob.glob(str(script_folder.absolute() / "*.kql"))
        if not files:
            logger.error(f"No script found in path {script_folder.absolute()}")
            return CommandResponse.fail()
        for _file in files[::-1]:
            file_path = Path(_file)
            logger.info(f"Found script {file_path} sending it to the database.")
            self.run(context=context, script_file=file_path, kusto_client=kusto_client)

    def run(
        self, context: dict, script_file: Path, kusto_client: KustoManagementClient
    ):
        resource_group_name = context["azure_resource_group_name"]
        adx_cluster_name = context["adx_cluster_name"]
        database_name = context["adx_database_name"]
        if script_file.suffix != ".kql":
            logger.warning(
                f"File {script_file.name} is not a kql file. Errors could happen."
            )
        script_name = f"{int(time.time() // 1)}-{script_file.name}"
        with open(script_file) as _script_file:
            logger.info(f"Reading {script_file}")
            script_content = _script_file.read().replace(
                "<database name>", database_name
            )
            logger.info("Sending script to database.")
            s = kusto_client.scripts.begin_create_or_update(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                database_name=database_name,
                script_name=script_name,
                parameters={"script_content": script_content},
                polling_interval=1,
            )
            try:
                with progressbar(
                    length=20, label="Waiting for script to finish"
                ) as bar:
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

import glob
import logging
import time

from pathlib import Path
from click import progressbar
from azure.mgmt.kusto import KustoManagementClient
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.core.exceptions import HttpResponseError
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


class AdxScriptService:

    def __init__(self, kusto_client: KustoManagementClient, state: dict = None) -> None:
        self.state = state
        self.kusto_client = kusto_client
        config = env.get_state_from_vault_by_platform(env.environ_id)
        self.babylon_client_id = config["babylon"]["client_id"]
        self.baby_client_secret = env.get_env_babylon(name="client", environ_id=env.environ_id)

    def get_all(self):
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]
        database_name = self.state["adx"]["database_name"]
        try:
            response = self.kusto_client.scripts.list_by_database(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                database_name=database_name,
            )
            scripts = [item.as_dict() for item in response]
            return scripts
        except Exception as exp:
            logger.warning(exp)
            return list()

    def run_folder(self, script_folder: Path):
        files = glob.glob(str(script_folder.absolute() / "*.kql"))
        if not files:
            logger.error(f"No script found in path {script_folder.absolute()}")
            return None
        for _file in files[::-1]:
            file_path = Path(_file)
            logger.info(f"Found script {file_path} sending it to the database.")
            self.run(script_file=file_path, kusto_client=self.kusto_client)

    def run(self, script_file: Path, script_id: str):
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]
        database_name = self.state["adx"]["database_name"]
        if script_file.suffix != ".kql":
            logger.warning(f"File {script_file.name} is not a kql file. Errors could happen.")
        script_name = script_id
        with open(script_file) as _script_file:
            logger.info(f"Reading {script_file}")
            script_content = _script_file.read()
            logger.info("Sending script to database.")
            try:
                s = self.kusto_client.scripts.begin_create_or_update(
                    resource_group_name=resource_group_name,
                    cluster_name=adx_cluster_name,
                    database_name=database_name,
                    script_name=script_name,
                    parameters={"script_content": script_content},
                    polling_interval=1,
                )
                with progressbar(length=20, label="Waiting for script to finish") as bar:
                    for _ in bar:
                        if not s.done():
                            s.wait(1)
                    while not s.done():
                        s.wait(1)
            except HttpResponseError as _resp_error:
                logger.error(_resp_error.message.split("\nMessage:")[1])
            logger.info("Successfully ran")

    def execute_query(self, script_file: Path, database_uri: str):
        adx_cluster_name = self.state["adx"]["cluster_name"]
        resource_location = str(self.state["azure"]['resource_location']).replace(" ", "").lower()
        database_uri = database_uri or f"https://{adx_cluster_name}.{resource_location}.kusto.windows.net"
        database_name = self.state["adx"]["database_name"]
        if script_file.suffix != ".kql":
            logger.warning(f"File {script_file.name} is not a kql file. Errors could happen.")
        with open(script_file) as _script_file:
            script_content = _script_file.read().replace("<database_name>", database_name)
            kbsc = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                aad_app_id=self.babylon_client_id,
                app_key=self.baby_client_secret,
                authority_id=env.tenant_id,
                connection_string=database_uri)
            kusto_client = KustoClient(kcsb=kbsc)
            try:
                s = kusto_client.execute_mgmt(database=database_name, query=script_content)
                logger.info(f"[adx] Sending ADX script '{script_file.name}' to Kusto database '{database_name}'")
                with progressbar(length=20, label="Waiting for script to finish") as bar:
                    for _ in bar:
                        if not s.primary_results:
                            time.sleep(1)
                    while not s.primary_results:
                        time.sleep(1)
            except Exception:
                logger.error(f"[adx] Syntax error in the script '{script_file}'")

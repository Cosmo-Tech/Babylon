import json
import logging

from click import progressbar
from datetime import timedelta
from Babylon.utils.checkers import check_ascii
from azure.mgmt.kusto.models import ReadWriteDatabase
from azure.mgmt.kusto.models import CheckNameRequest
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


class AdxDatabaseService:

    def __init__(self, kusto_client: KustoManagementClient, state: dict = None) -> None:
        self.kusto_client = kusto_client
        self.state = state

    def create(
        self,
        name: str,
        retention: int,
    ):
        if name:
            check_ascii(name)
        organization_id = self.state["api"]["organization_id"]
        workspace_key = self.state["api"]["workspace_key"]
        resource_location = self.state["azure"]["resource_location"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]

        # cache period by default 31 days
        params_database = ReadWriteDatabase(
            location=resource_location,
            soft_delete_period=timedelta(days=retention),
            hot_cache_period=timedelta(days=31),
        )
        name = name or f"{organization_id}-{workspace_key}"
        try:
            name_request = CheckNameRequest(
                name=name, type="Microsoft.Kusto/clusters/databases"
            )
            name_result = self.kusto_client.databases.check_name_availability(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                resource_name=name_request,
                content_type="application/json",
            )
            _ret: list[str] = []
            if not name_result.name_available:
                for k, v in name_result.as_dict().items():
                    _ret.append(f"{k}: {v}")
                logger.error("\n".join(_ret))
                return CommandResponse.fail()
        except Exception:
            return CommandResponse.fail()

        poller = self.kusto_client.databases.begin_create_or_update(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=name,
            parameters=params_database,
            content_type="application/json",
        )
        poller.wait()
        # check if done
        if not poller.done():
            return CommandResponse.fail()
        # batabase created

        # init bd with policies
        script_name = f"initdb-{name}.kusto"
        batching_policy = json.dumps({"MaximumBatchingTimeSpan": "00:00:10"})
        script_content = (
            f".alter database ['{name}'] policy streamingingestion disable\n"
        )
        script_content += "//\n"
        script_content += f".alter-merge database ['{name}'] policy retention softdelete = {retention}d"
        script_content += "//\n"
        script_content += (
            f".alter database ['{name}'] policy ingestionbatching '{batching_policy}'"
        )
        s = self.kusto_client.scripts.begin_create_or_update(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=name,
            content_type="application/json",
            script_name=script_name,
            parameters={"script_content": script_content},
            polling_interval=1,
        )
        try:
            with progressbar(
                length=20, label="Waiting for init script to finish"
            ) as bar:
                for _ in bar:
                    if not s.done():
                        s.wait(1)
                while not s.done():
                    s.wait(1)
        except Exception as _resp_error:
            logger.error(_resp_error.message.split("\nMessage:")[1])
            return CommandResponse.fail()
        self.kusto_client.scripts.begin_delete(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=name,
            script_name=script_name,
        )
        logger.info("Successfully ran")
        # env.configuration.set_var(
        #     resource_id=ctx.parent.parent.command.name,
        #     var_name="database_name",
        #     var_value=name.lower(),
        # )
        _ret: list[str] = [f"Provisioning state: {poller.result().provisioning_state}"]
        logger.info("\n".join(_ret))

    def delete(
        self,
        current: bool,
        name: str,
    ):
        resource_group_name = self.state["azure"]["resource_group_name"]
        adx_cluster_name = self.state["adx"]["cluster_name"]
        database_name = self.state["adx"]["database_name"] if current else name
        try:
            self.kusto_client.databases.get(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                database_name=database_name,
            )
        except Exception as ex:
            logger.error(ex)
            return CommandResponse.fail()

        poller = self.kusto_client.databases.begin_delete(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=database_name,
        )
        poller.wait()
        if not poller.done():
            return CommandResponse.fail()
        if poller.status() == "Succeeded":
            _ret: list[str] = ["Provisioning state: Deleted"]
        logger.info("\n".join(_ret))

    def get(
        self,
        name: str,
    ):
        adx_cluster_name = self.state["adx"]["cluster_name"]
        if not name:
            logger.error(f"Current value: '{self.state['adx_database_name']}'")
        adx_database_name = name or self.state["adx"]["database_name"]
        if not adx_database_name:
            logger.error("Database name is missing")
            return CommandResponse.fail()
        resource_group_name = self.state["azure"]["resource_group_name"]
        try:
            database = self.kusto_client.databases.get(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                database_name=adx_database_name,
            )
            _ret: list[str] = []
            for k, v in database.as_dict().items():
                _ret.append(f"{k}:{v}")
            logger.info("\n".join(_ret))
            # env.configuration.set_var(
            #     resource_id=ctx.parent.parent.command.name,
            #     var_name="database_name",
            #     var_value=adx_database_name,
            # )
            return CommandResponse.success()
        except Exception as ex:
            logger.info(ex)
            return CommandResponse.fail()

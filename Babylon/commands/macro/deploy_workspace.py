import json
import sys
import pathlib

from logging import getLogger

from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient

from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.service.api import ArmService
from azure.mgmt.authorization import AuthorizationManagementClient
from Babylon.commands.azure.permission.service.api import AzureIamService
from Babylon.commands.azure.adx.script.service.api import AdxScriptService
from Babylon.commands.azure.adx.consumer.service.api import AdxConsumerService
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
from Babylon.utils.credentials import get_azure_credentials, get_azure_token, get_powerbi_token
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.commands.azure.adx.permission.service.api import AdxPermissionService
from Babylon.commands.azure.adx.connections.service.api import AdxConnectionService
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.commands.powerbi.workspace.user.service.api import (
    AzurePowerBIWorkspaceUserService,
)

# from posixpath import basename
# from azure.mgmt.kusto import KustoManagementClient
# from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.commands.api.workspaces.service.api import WorkspaceService
# from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
# from Babylon.commands.api.solutions.handler.service.api import SolutionHandleService

logger = getLogger("Babylon")
env = Environment()


def deploy_workspace(file_content: str, deploy_dir: pathlib.Path) -> bool:
    print("Workspace deployment")
    state = env.retrieve_state_func()
    ext_args = dict(azure_function_secret="")
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
    azure_credential = get_azure_credentials()
    service_state = state["services"]
    subscription_id = state["services"]["azure"]["subscription_id"]
    service_state["api"]["organization_id"] = "o-qwy2y8eyz8k"
    service_state["api"]["workspace_key"] = "w-test"
    service_state["adx"]["database_name"] = "o-qwy2y8eyz8k-w-test"
    payload: dict = file_content.get("spec").get("payload")
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    azure_token = get_azure_token("csm_api")
    workspace_svc = WorkspaceService(
        azure_token=azure_token, spec=spec, state=service_state
    )
    if not service_state["api"]["workspace_id"]:
        response = workspace_svc.create()
        solution = response.json()
    else:
        response = workspace_svc.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = workspace_svc.update_security(old_security=old_security)
        response_json["security"] = security_spec
        solution = response_json
        logger.info(solution)
    sidecars = content.get("spec")["sidecars"]
    eventhub_section = sidecars["azure"].get("eventhub", {})
    adx_section = sidecars["azure"].get("adx", {})
    powerbi_section = sidecars["azure"].get("powerbi", {})
    if powerbi_section:
        workspace_powerbi = powerbi_section.get("workspace", {})
        if workspace_powerbi:
            po_token = get_powerbi_token()
            powerbi_svc = AzurePowerBIWorkspaceService(
                powerbi_token=po_token, state=service_state
            )
            name = workspace_powerbi.get("name", "")
            if not name:
                logger.error("name not found")
                sys.exit(1)
            workspaceli_list_name = powerbi_svc.get_all(filter="[].name")
            if name not in workspaceli_list_name:
                powerbi_svc.create(name=name)
            logger.info(f"workspace '{name}' already exists")
            work_obj = powerbi_svc.get_by_name_or_id(name=name)
            user_svc = AzurePowerBIWorkspaceUserService(
                powerbi_token=po_token, state=service_state
            )
            existing_permissions = user_svc.get_all(
                workspace_id=work_obj.get("id"), filter="[].identifier"
            )
            spec_permissions = workspace_powerbi.get("permissions", [])
            if len(spec_permissions):
                ids = [i.get("identifier") for i in spec_permissions]
                for g in spec_permissions:
                    if g.get("identifier") in existing_permissions:
                        user_svc.update(
                            workspace_id=work_obj.get("id"),
                            right=g.get("rights"),
                            email=g.get("identifier"),
                            type=g.get("type"),
                        )
                    if g.get("identifier") not in existing_permissions:
                        user_svc.add(
                            workspace_id=work_obj.get("id"),
                            right=g.get("rights"),
                            email=g.get("identifier"),
                            type=g.get("type"),
                        )
                for s in existing_permissions:
                    if s not in ids:
                        if s != state["services"]["babylon"]["principal_id"]:
                            user_svc.delete(
                                workspace_id=work_obj.get("id"),
                                email=s,
                                force_validation=True,
                            )
            spec_dash = workspace_powerbi.get("reports", [])
            if len(spec_dash):
                for r in spec_dash:
                    rtype = r.get("type")
                    name = r.get("name")
                    path = r.get("path")
                    path_report = pathlib.Path(deploy_dir) / f"{path}"
                    if not path_report.exists():
                        logger.error(f"report '{path_report}' not found")
                    if path_report.exists():
                        report_svc = AzurePowerBIReportService(
                            powerbi_token=po_token, state=service_state
                        )
                        report_svc.upload(
                            workspace_id=work_obj.get("id"),
                            pbix_filename=path_report,
                            report_name=name,
                            report_type=rtype,
                            override=True,
                        )
    if adx_section:
        created = False
        ok = True
        kusto_client = KustoManagementClient(
            credential=azure_credential, subscription_id=subscription_id
        )
        adx_svc = AdxDatabaseService(kusto_client=kusto_client, state=state["services"])
        state["services"]["api"]["organization_id"] = "o-qwy2y8eyz8k"
        state["services"]["api"]["workspace_key"] = "w-test"
        name = f"{state['services']['api']['organization_id']}-{state['services']['api']['workspace_key']}"
        available = adx_svc.check(name=name)
        if available:
            created = adx_svc.create(
                name=name, retention=adx_section.get("database").get("retention", 365)
            )
            if created:
                available = False
        if not available:
            permission_svc = AdxPermissionService(
                kusto_client=kusto_client, state=service_state
            )
            existing_permissions = permission_svc.get_all()
            existing_ids = [ent.get("principal_id") for ent in existing_permissions]
            spec_permissions: list = adx_section["database"].get("permissions", [])
            if len(spec_permissions):
                ids = [i.get("principal_id") for i in spec_permissions]
                for g in spec_permissions:
                    if g.get("principal_id") in existing_ids:
                        deleted = permission_svc.delete(
                            g.get("principal_id"), force_validation=True
                        )
                        if deleted:
                            permission_svc.set(
                                g.get("principal_id"), g.get("type"), role=g.get("role")
                            )
                    if g.get("principal_id") not in existing_ids:
                        permission_svc.set(
                            g.get("principal_id"), g.get("type"), role=g.get("role")
                        )
                for s in existing_ids:
                    if s not in ids:
                        if s != state["services"]["babylon"]["client_id"]:
                            permission_svc.delete(s, force_validation=True)
        if ok:
            scripts_svc = AdxScriptService(
                kusto_client=kusto_client, state=service_state
            )
            script_list = scripts_svc.get_all()
            scripts_spec: list[dict] = adx_section.get("database").get("scripts", [])
            if len(scripts_spec):
                for s in scripts_spec:
                    t = list(
                        filter(lambda x: s.get("id") in str(x.get("id")), script_list)
                    )
                    if not len(t):
                        name = s.get("name")
                        path_end = s.get("path")
                        path_abs = pathlib.Path(deploy_dir) / f"{path_end}/{name}"
                        scripts_svc.run(path_abs.absolute(), script_id=s.get("id"))
    if eventhub_section:
        kusto_client = KustoManagementClient(
            credential=azure_credential, subscription_id=subscription_id
        )
        arm_client = ResourceManagementClient(
            credential=azure_credential, subscription_id=subscription_id
        )
        iam_client = AuthorizationManagementClient(credential=azure_credential, subscription_id=subscription_id)
        service_state["api"]["organization_id"] = "o-qwy2y8eyz8k"
        adx_svc = ArmService(arm_client=arm_client, state=service_state)
        adx_svc.run(deployment_name="eventhubtestniabldo", file="eventhub_deploy.json")
        arm_svc = AzureIamService(iam_client=iam_client, state=service_state)
        principal_id = service_state['adx']['cluster_principal_id']
        resource_type = "Microsoft.EventHub/Namespaces"
        resource_name = f"{service_state['api']['organization_id']}-{service_state['api']['workspace_key']}"
        role_id = service_state['azure']['eventhub_built_data_receiver']
        arm_svc.set(
            principal_id=principal_id,
            resource_name=resource_name,
            resource_type=resource_type,
            role_id=role_id
        )
        principal_id = service_state['platform']['principal_id']
        resource_type = "Microsoft.EventHub/Namespaces"
        resource_name = f"{service_state['api']['organization_id']}-{service_state['api']['workspace_key']}"
        role_id = service_state['azure']['eventhub_built_data_sender']
        arm_svc.set(
            principal_id=principal_id,
            resource_name=resource_name,
            resource_type=resource_type,
            role_id=role_id
        )
        principal_id = service_state['babylon']['principal_id']
        resource_type = "Microsoft.EventHub/Namespaces"
        resource_name = f"{service_state['api']['organization_id']}-{service_state['api']['workspace_key']}"
        role_id = service_state['azure']['eventhub_built_data_sender']
        arm_svc.set(
            principal_id=principal_id,
            resource_name=resource_name,
            resource_type=resource_type,
            role_id=role_id
        )
        consumers = eventhub_section.get("consumers", [])
        ent_accepted = [
            "ProbesMeasures",
            "ScenarioMetadata",
            "ScenarioRun",
            "ScenarioRunMetadata",
        ]
        if len(consumers):
            service_event = AdxConsumerService(state=service_state)
            for ent in ent_accepted:
                spec_listing = [
                    k.get("displayName")
                    for k in list(filter(lambda x: x.get("entity") == ent, consumers))
                ]
                existing_consumers = service_event.get_all(event_hub_name=ent)
                for t in spec_listing:
                    if t not in existing_consumers:
                        service_event.add(name=t, event_hub_name=ent)
                for s in existing_consumers:
                    if s not in spec_listing:
                        service_event.delete(name=s, event_hub_name=ent)
        connectors = eventhub_section.get("connectors", [])
        if len(connectors):
            service_conn = AdxConnectionService(
                kusto_client=kusto_client, state=service_state
            )
            spec_databases = list(set([k.get("database_target") for k in connectors]))
            for db in spec_databases:
                existing_connectors = service_conn.get_all(database_name=db)
                existing_conn_names = [
                    dict(
                        table=k.get("table_name"),
                        database=k.get("name").split("/")[-2],
                    )
                    for k in existing_connectors
                ]
                spec_conn = [
                    dict(
                        table=k.get("table_name"),
                        database=k.get("database_target"),
                        data=k,
                    )
                    for k in connectors
                ]
                for ch in spec_conn:
                    t = dict(table=ch.get("table"), database=ch.get("database"))
                    if t not in existing_conn_names:
                        k = ch.get("data")
                        compression_value = k.get("compression")
                        connection_name = k.get("connection_name")
                        consumer_group = k.get("consumer_group")
                        database_name = k.get("database_target")
                        data_format = k.get("format")
                        table_name = k.get("table_name")
                        mapping = k.get("mapping")
                        service_conn.create(
                            compression_value=compression_value,
                            connection_name=connection_name,
                            consumer_group=consumer_group,
                            database_name=database_name,
                            data_format=data_format,
                            table_name=table_name,
                            mapping=mapping,
                        )
                for hc in existing_conn_names:
                    if hc.get("table") not in [k.get("table") for k in spec_conn]:
                        to_delete = list(
                            filter(
                                lambda x: x.get("table_name") == hc.get("table"),
                                existing_connectors,
                            )
                        )
                        if to_delete:
                            connection_name = to_delete[-1]['name'].split("/")[-1]
                            service_conn.delete(database_name=db, connection_name=connection_name)
    return True

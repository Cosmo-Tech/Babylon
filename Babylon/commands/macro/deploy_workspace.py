import os
import sys
import json
import pathlib

from logging import getLogger
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.services.api import ArmService
from azure.mgmt.authorization import AuthorizationManagementClient
from Babylon.commands.azure.adx.services.script import AdxScriptService
from Babylon.commands.api.workspaces.services.api import WorkspaceService
from Babylon.commands.azure.permission.services.api import AzureIamService
from Babylon.commands.azure.adx.services.consumer import AdxConsumerService
from Babylon.commands.azure.adx.services.database import AdxDatabaseService
from Babylon.commands.azure.adx.services.connection import AdxConnectionService
from Babylon.commands.azure.adx.services.permission import AdxPermissionService
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.credentials import get_azure_credentials, get_azure_token, get_powerbi_token
from Babylon.commands.powerbi.workspace.user.service.api import (
    AzurePowerBIWorkspaceUserService, )

logger = getLogger("Babylon")
env = Environment()


def deploy_workspace(file_content: str, deploy_dir: pathlib.Path) -> bool:
    logger.info("Workspace deployment")
    platform_url = env.set_ns_from_yaml(content=file_content)
    state = env.retrieve_state_func()
    state['services']['api']['url'] = platform_url
    azure_credential = get_azure_credentials()
    subscription_id = state["services"]["azure"]["subscription_id"]
    organization_id = state['services']['api']['organization_id']
    workspace_key = state['services']['api']['workspace_key']
    azf_secret = env.get_project_secret(
        organization_id=organization_id,
        workspace_key=workspace_key,
        name="azf")
    ext_args = dict(azure_function_secret=azf_secret)
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
    payload: dict = content.get("spec").get("payload")
    work_key = payload.get('key')
    state["services"]["api"]["workspace_key"] = work_key
    state['services']["adx"]["database_name"] = f"{organization_id}-{work_key}"
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    azure_token = get_azure_token("csm_api")
    workspace_svc = WorkspaceService(azure_token=azure_token, spec=spec, state=state.get('services'))
    if not state['services']["api"]["workspace_id"]:
        logger.info("Creating workspace...")
        response = workspace_svc.create()
        workspace = response.json()
        logger.info(f"Workspace {workspace.get('id')} successfully created...")
        logger.info(json.dumps(workspace, indent=2))
    else:
        logger.info(f"Updating workspace {state['services']['api']['workspace_id']}...")
        response = workspace_svc.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = workspace_svc.update_security(old_security=old_security)
        response_json["security"] = security_spec
        workspace = response_json
        logger.info(json.dumps(workspace, indent=2))
    state["services"]["api"]["workspace_id"] = workspace.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    # update sidecars
    sidecars = content.get("spec")["sidecars"]
    eventhub_section = sidecars["azure"].get("eventhub", {})
    adx_section = sidecars["azure"].get("adx", {})
    powerbi_section = sidecars["azure"].get("powerbi", {})
    if powerbi_section:
        workspace_powerbi = powerbi_section.get("workspace", {})
        if workspace_powerbi:
            po_token = get_powerbi_token()
            powerbi_svc = AzurePowerBIWorkspaceService(powerbi_token=po_token, state=state.get('services'))
            name = workspace_powerbi.get("name", "")
            if not name:
                logger.error("Name of powerBI workspace not found")
                sys.exit(1)
            workspaceli_list_name = powerbi_svc.get_all(filter="[].name")
            if name not in workspaceli_list_name:
                logger.info(f"creating powerBI workspace... {name}")
                w = powerbi_svc.create(name=name)
                state['services']['powerbi']['workspace.id'] = w.get('id')
                env.store_state_in_local(state)
                env.store_state_in_cloud(state)
            else:
                logger.info(f"PowerBI workspace '{name}' already exists")
            work_obj = powerbi_svc.get_by_name_or_id(name=name)
            state['services']['powerbi']['workspace.id'] = work_obj.get('id')
            env.store_state_in_local(state)
            env.store_state_in_cloud(state)
            user_svc = AzurePowerBIWorkspaceUserService(powerbi_token=po_token, state=state.get('services'))
            existing_permissions = user_svc.get_all(workspace_id=work_obj.get("id"), filter="[].identifier")
            spec_permissions = workspace_powerbi.get("permissions", [])
            if len(spec_permissions):
                ids = [i.get("identifier") for i in spec_permissions]
                for g in spec_permissions:
                    if g.get("identifier") in existing_permissions:
                        logger.info(f"Updating permissions for {g.get('identifier')}")
                        user_svc.update(
                            workspace_id=work_obj.get("id"),
                            right=g.get("rights"),
                            email=g.get("identifier"),
                            type=g.get("type"),
                        )
                    if g.get("identifier") not in existing_permissions:
                        logger.info(f"Creating permissions for {g.get('identifier')}")
                        user_svc.add(
                            workspace_id=work_obj.get("id"),
                            right=g.get("rights"),
                            email=g.get("identifier"),
                            type=g.get("type"),
                        )
                for s in existing_permissions:
                    if s not in ids:
                        if s != state["services"]["babylon"]["principal_id"]:
                            logger.info(f"Deleting permissions for {g.get('identifier')}")
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
                        logger.error(f"Report '{path_report}' not found")
                    if path_report.exists():
                        report_svc = AzurePowerBIReportService(powerbi_token=po_token, state=state.get('services'))
                        report_svc.upload(
                            workspace_id=work_obj.get("id"),
                            pbix_filename=path_report,
                            report_name=name,
                            report_type=rtype,
                            override=True,
                        )
                        logger.info(f"Report {name} successfully imported")
    if adx_section:
        ok = True
        kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
        adx_svc = AdxDatabaseService(kusto_client=kusto_client, state=state["services"])
        name = f"{organization_id}-{work_key}"
        available = adx_svc.check(name=name)
        to_create = adx_section.get('database').get('create', True)
        if available and to_create:
            created = adx_svc.create(name=name, retention=adx_section.get("database").get("retention", 365))
            if created:
                available = False
        if not available:
            permission_svc = AdxPermissionService(kusto_client=kusto_client, state=state.get('services'))
            existing_permissions = permission_svc.get_all()
            existing_ids = [ent.get("principal_id") for ent in existing_permissions]
            spec_permissions: list = adx_section["database"].get("permissions", [])
            if len(spec_permissions):
                ids = [i.get("principal_id") for i in spec_permissions]
                for g in spec_permissions:
                    if g.get("principal_id") in existing_ids:
                        deleted = permission_svc.delete(g.get("principal_id"), force_validation=True)
                        if deleted:
                            permission_svc.set(g.get("principal_id"), g.get("type"), role=g.get("role"))
                    if g.get("principal_id") not in existing_ids:
                        permission_svc.set(g.get("principal_id"), g.get("type"), role=g.get("role"))
                for s in existing_ids:
                    if s not in ids:
                        if s != state["services"]["babylon"]["client_id"]:
                            permission_svc.delete(s, force_validation=True)
        if ok:
            scripts_svc = AdxScriptService(kusto_client=kusto_client, state=state.get('services'))
            script_list = scripts_svc.get_all()
            scripts_spec: list[dict] = adx_section.get("database").get("scripts", [])
            if len(scripts_spec):
                for s in scripts_spec:
                    t = list(filter(lambda x: s.get("id") in str(x.get("id")), script_list))
                    if not len(t):
                        name = s.get("name")
                        path_end = s.get("path")
                        path_abs = pathlib.Path(deploy_dir) / f"{path_end}/{name}"
                        scripts_svc.run(path_abs.absolute(), script_id=s.get("id"))
    if eventhub_section:
        kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
        arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
        iam_client = AuthorizationManagementClient(credential=azure_credential, subscription_id=subscription_id)
        adx_svc = ArmService(arm_client=arm_client, state=state.get('services'))
        deployment_name = f"{organization_id}-{work_key}"
        adx_svc.run(deployment_name=deployment_name, file="eventhub_deploy.json")
        arm_svc = AzureIamService(iam_client=iam_client, state=state.get('services'))
        principal_id = state['services']['adx']['cluster_principal_id']
        resource_type = "Microsoft.EventHub/Namespaces"
        resource_name = f"{organization_id}-{work_key}"
        role_id = state['services']['azure']['eventhub_built_data_receiver']
        arm_svc.set(principal_id=principal_id,
                    resource_name=resource_name,
                    resource_type=resource_type,
                    role_id=role_id)
        principal_id = state['services']['platform']['principal_id']
        resource_type = "Microsoft.EventHub/Namespaces"
        resource_name = f"{organization_id}-{work_key}"
        role_id = state['services']['azure']['eventhub_built_data_sender']
        arm_svc.set(principal_id=principal_id,
                    resource_name=resource_name,
                    resource_type=resource_type,
                    role_id=role_id)
        principal_id = state['services']['babylon']['principal_id']
        resource_type = "Microsoft.EventHub/Namespaces"
        resource_name = f"{organization_id}-{work_key}"
        role_id = state['services']['azure']['eventhub_built_data_sender']
        arm_svc.set(principal_id=principal_id,
                    resource_name=resource_name,
                    resource_type=resource_type,
                    role_id=role_id)
        consumers = eventhub_section.get("consumers", [])
        ent_accepted = [
            "ProbesMeasures",
            "ScenarioMetadata",
            "ScenarioRun",
            "ScenarioRunMetadata",
        ]
        if len(consumers):
            service_event = AdxConsumerService(state=state.get('services'))
            for ent in ent_accepted:
                spec_listing = [k.get("displayName") for k in list(filter(lambda x: x.get("entity") == ent, consumers))]
                existing_consumers = service_event.get_all(event_hub_name=ent)
                for t in spec_listing:
                    if t not in existing_consumers:
                        service_event.add(name=t, event_hub_name=ent)
                for s in existing_consumers:
                    if s not in spec_listing:
                        service_event.delete(name=s, event_hub_name=ent)
        connectors = eventhub_section.get("connectors", [])
        if len(connectors):
            service_conn = AdxConnectionService(kusto_client=kusto_client, state=state.get('services'))
            spec_databases = list(set([k.get("database_target") for k in connectors]))
            for db in spec_databases:
                existing_connectors = service_conn.get_all(database_name=db)
                existing_conn_names = [
                    dict(
                        table=k.get("table_name"),
                        database=k.get("name").split("/")[-2],
                    ) for k in existing_connectors
                ]
                spec_conn = [
                    dict(
                        table=k.get("table_name"),
                        database=k.get("database_target"),
                        data=k,
                    ) for k in connectors
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
                        to_delete = list(filter(
                            lambda x: x.get("table_name") == hc.get("table"),
                            existing_connectors,
                        ))
                        if to_delete:
                            connection_name = to_delete[-1]['name'].split("/")[-1]
                            service_conn.delete(database_name=db, connection_name=connection_name)
    run_scripts = sidecars.get("run_scripts")
    if run_scripts:
        data = run_scripts.get("post_deploy.sh", "")
        if data:
            os.system(data)
    if not workspace.get("id"):
        sys.exit(1)

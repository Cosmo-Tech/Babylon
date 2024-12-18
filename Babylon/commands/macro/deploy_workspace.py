import os
import sys
import json
import click
import pathlib

from logging import getLogger
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.services.arm_api_svc import ArmService
from azure.mgmt.authorization import AuthorizationManagementClient
from Babylon.commands.azure.adx.services.adx_script_svc import AdxScriptService
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.commands.azure.permission.services.iam_api_svc import AzureIamService
from Babylon.commands.azure.adx.services.adx_consumer_svc import AdxConsumerService
from Babylon.commands.azure.adx.services.adx_database_svc import AdxDatabaseService
from Babylon.commands.azure.adx.services.adx_connection_svc import AdxConnectionService
from Babylon.commands.azure.adx.services.adx_permission_svc import AdxPermissionService
from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import (
    AzurePowerBIReportService, )
from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import (
    AzurePowerBIDatasetService, )
from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import (
    AzurePowerBIWorkspaceService, )
from Babylon.commands.powerbi.dataset.services.powerbi_params_svc import (
    AzurePowerBIParamsService, )
from Babylon.utils.credentials import (
    get_azure_credentials,
    get_azure_token,
    get_default_powerbi_token,
)
from Babylon.commands.powerbi.workspace.services.powerb__worskapce_users_svc import (
    AzurePowerBIWorkspaceUserService, )

logger = getLogger("Babylon")
env = Environment()


def deploy_workspace(namespace: str, file_content: str, deploy_dir: pathlib.Path, payload_only: bool) -> bool:
    _ret = [""]
    _ret.append("Workspace deployment")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    platform_url = env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func(state_id=env.state_id)
    state["services"]["api"]["url"] = platform_url
    state["services"]["azure"]["tenant_id"] = env.tenant_id
    vars = env.get_variables()
    metadata = env.get_metadata(vars=vars, content=file_content, state=state)
    workspace_key = metadata.get(
        "workspace_key",
        vars.get("workspace_key", state["services"]["api"]["workspace_key"]),
    )
    state["services"]["api"]["workspace_key"] = workspace_key
    if metadata.get("selector", ""):
        state["services"]["api"]["organization_id"] = metadata["selector"].get("organization_id", "")
        state["services"]["api"]["solution_id"] = metadata["selector"].get("solution_id", "")
    else:
        if (not state["services"]["api"]["organization_id"] and not state["services"]["api"]["solution_id"]):
            logger.error(
                "Selector verification failed. Please check the selector field for correctness: %s",
                metadata.get("selector"),
            )
    subscription_id = state["services"]["azure"]["subscription_id"]
    organization_id = state["services"]["api"]["organization_id"]
    azf_secret = env.get_project_secret(organization_id=organization_id, workspace_key=workspace_key, name="azf")
    ext_args = dict(azure_function_secret=azf_secret)
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
    payload: dict = content.get("spec").get("payload")
    state["services"]["adx"]["database_name"] = f"{organization_id}-{workspace_key}"
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    azure_token = get_azure_token("csm_api")
    workspace_svc = WorkspaceService(azure_token=azure_token, spec=spec, state=state.get("services"))
    if not state["services"]["api"]["workspace_id"]:
        logger.info("[api] creating workspace")
        response = workspace_svc.create()
        if not response:
            sys.exit(1)
        workspace = response.json()
        logger.info(f"[api] workspace {workspace.get('id')} successfully created")
        logger.info(json.dumps(workspace, indent=2))
        state["services"]["api"]["workspace_id"] = workspace.get("id")
    else:
        logger.info(f"[api] updating workspace {state['services']['api']['workspace_id']}")
        response = workspace_svc.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = workspace_svc.update_security(old_security=old_security)
        response_json["security"] = security_spec
        workspace = response_json
        logger.info(json.dumps(workspace, indent=2))
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    # update sidecars
    sidecars = content.get("spec").get("sidecars", None)
    if (content.get("spec").get("payload") is not None
            and content.get("spec").get("payload").get("webApp") is not None):
        workspaceCharts = (content.get("spec").get("payload").get("webApp").get("options").get("charts") or None)
    else:
        workspaceCharts = None
    if sidecars and not payload_only:
        eventhub_section = sidecars.get("azure").get("eventhub", {})
        adx_section = sidecars["azure"].get("adx", {})
        powerbi_section = sidecars["azure"].get("powerbi", {})
        if powerbi_section:
            workspace_powerbi = powerbi_section.get("workspace", {})
            if workspace_powerbi:
                po_token = get_default_powerbi_token()
                powerbi_svc = AzurePowerBIWorkspaceService(powerbi_token=po_token, state=state.get("services"))
                name = workspace_powerbi.get("name", "")
                if not name:
                    logger.error("[powerbi] PowerBI workspace name is mandatory")
                    sys.exit(1)
                workspaceli_list_name = powerbi_svc.get_all(filter="[].name")
                if (workspaceli_list_name is None) or (workspaceli_list_name is not None
                                                       and name not in workspaceli_list_name):
                    logger.info(f"[powerbi] creating PowerBI Workspace {name}")
                    w = powerbi_svc.create(name=name)
                    state["services"]["powerbi"]["workspace.id"] = w.get("id")
                    state["services"]["powerbi"]["workspace.name"] = w.get("name")
                    env.store_state_in_local(state)
                    if env.remote:
                        env.store_state_in_cloud(state)
                else:
                    logger.info(f"[powerbi] PowerBI Workspace '{name}' already exists")
                work_obj = powerbi_svc.get_by_name_or_id(name=name)
                if work_obj:
                    state["services"]["powerbi"]["workspace.id"] = work_obj.get("id")
                    state["services"]["powerbi"]["workspace.name"] = work_obj.get("name")
                    env.store_state_in_local(state)
                    if env.remote:
                        env.store_state_in_cloud(state)
                user_svc = AzurePowerBIWorkspaceUserService(powerbi_token=po_token, state=state.get("services"))
                work_obj_id = state["services"]["powerbi"]["workspace.id"]
                existing_permissions = user_svc.get_all(workspace_id=work_obj_id, filter="[].identifier")
                spec_permissions = workspace_powerbi.get("permissions", [])
                if len(spec_permissions):
                    ids = [i.get("identifier") for i in spec_permissions]
                    for g in spec_permissions:
                        if g.get("identifier") in existing_permissions:
                            logger.info(f"[powerbi] updating permissions for {g.get('identifier')}")
                            user_svc.update(
                                workspace_id=work_obj.get("id"),
                                right=g.get("rights"),
                                email=g.get("identifier"),
                                type=g.get("type"),
                            )
                        if g.get("identifier") not in existing_permissions:
                            logger.info(f"[powerbi] creating permissions for {g.get('identifier')}")
                            user_svc.add(
                                workspace_id=work_obj.get("id"),
                                right=g.get("rights"),
                                email=g.get("identifier"),
                                type=g.get("type"),
                            )
                    for s in existing_permissions:
                        if s not in ids:
                            if s != state["services"]["babylon"]["principal_id"]:
                                logger.info(f"[powerbi] deleting permissions for {g.get('identifier')}")
                                user_svc.delete(
                                    workspace_id=work_obj.get("id"),
                                    email=s,
                                    force_validation=True,
                                )
                spec_dash = workspace_powerbi.get("reports", [])
                dashboard_view = dict()
                scenario_view = dict()
                if len(spec_dash):
                    for r in spec_dash:
                        rtype = r.get("type")
                        name = r.get("name")
                        path = r.get("path")
                        rtag = r.get("tag")
                        params = r.get("parameters", [])
                        path_report = pathlib.Path(deploy_dir) / f"{path}"
                        if not path_report.exists():
                            logger.warning(f"[powerbi] report '{path_report}' not found")
                        if path_report.exists():
                            parameters_svc = AzurePowerBIParamsService(powerbi_token=po_token,
                                                                       state=state.get("services"))
                            report_svc = AzurePowerBIReportService(powerbi_token=po_token, state=state.get("services"))
                            report_obj, custom_obj = report_svc.upload(
                                workspace_id=work_obj.get("id"),
                                pbix_filename=path_report,
                                report_name=name,
                                report_type=rtype,
                                override=True,
                            )

                            if workspaceCharts is not None:

                                if not rtag:
                                    logger.warning("[powerbi] Tag is missing in this report")
                                else:
                                    if rtype == "dashboard":
                                        dashboard_view[rtag] = custom_obj.get("reportId")
                                        allDashboardsViews = workspaceCharts.get("dashboardsView")
                                        # set the good value of reportId in the reports objects inside dashboardsView
                                        filteredTitles = list(
                                            filter(
                                                lambda x: x.get("reportTag") is not None and x.get("reportTag") == rtag,
                                                allDashboardsViews,
                                            ))
                                        if not filteredTitles:
                                            logger.warning(
                                                "[powerbi] Report tag is not found in dashboardsView Section")
                                        else:
                                            for item in filteredTitles:
                                                item["reportId"] = custom_obj.get("reportId")

                                    if rtype == "scenario":
                                        scenario_view[rtag] = custom_obj.get("reportId")
                                        allScenariosViews = workspaceCharts.get("scenarioView")
                                        scenarioWithThistag = False
                                        # set the good value of reportId in the reports objects inside scenarioView
                                        for scenario in allScenariosViews:
                                            if isinstance(scenario, dict):
                                                if (scenario.get("reportTag") is not None
                                                        and scenario.get("reportTag") == rtag):
                                                    scenario["reportId"] = (custom_obj.get("reportId"))
                                                    scenarioWithThistag = True
                                            else:
                                                scenarioData = allScenariosViews.get(scenario, {})
                                                if (scenarioData.get("reportTag") is not None
                                                        and scenarioData.get("reportTag") == rtag):
                                                    scenarioData["reportId"] = (custom_obj.get("reportId"))
                                                    scenarioWithThistag = True
                                        if not scenarioWithThistag:
                                            logger.warning("[powerbi] Report tag is not found in scenarioView Section")

                            for d in report_obj.get("datasets", []):
                                if d:
                                    dataset_svc = AzurePowerBIDatasetService(
                                        powerbi_token=po_token,
                                        state=state.get("services"),
                                    )
                                    dataset_svc.take_over(
                                        workspace_id=work_obj.get("id"),
                                        dataset_id=d.get("id"),
                                    )
                                    parameters_svc = AzurePowerBIParamsService(
                                        powerbi_token=po_token,
                                        state=state.get("services"),
                                    )
                                    if len(params):
                                        parameters_svc.update(
                                            workspace_id=work_obj.get("id"),
                                            dataset_id=d.get("id"),
                                            params=params,
                                        )
                            logger.info(f"[powerbi] report {name} successfully imported")
                state["services"]["powerbi"]["dashboard_view"] = dashboard_view
                state["services"]["powerbi"]["scenario_view"] = scenario_view
                env.store_state_in_local(state)
                if env.remote:
                    env.store_state_in_cloud(state)
        if workspaceCharts is not None and powerbi_section:
            content.get("spec").get("payload").get("webApp").get("options").get(
                "charts")["workspaceId"] = state["services"]["powerbi"]["workspace.id"]
            logger.info(
                f"[powerbi] updating workspace {state['services']['api']['workspace_id']} with all powerbi reports")
            payloadUpdated: dict = content.get("spec").get("payload")
            specUpdated = dict()
            specUpdated["payload"] = json.dumps(payloadUpdated, indent=2, ensure_ascii=True)
            workspace_svc.update_with_payload(specUpdated)
        azure_credential = get_azure_credentials()
        if adx_section:
            ok = True
            kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
            adx_svc = AdxDatabaseService(kusto_client=kusto_client, state=state["services"])
            name = f"{organization_id}-{workspace_key}"
            available = adx_svc.check(name=name)
            to_create = adx_section.get("database").get("create", True)
            if available and to_create:
                logger.info("[adx] creating or updating adx database")
                created = adx_svc.create(
                    name=name,
                    retention=adx_section.get("database").get("retention", 365),
                )
                if created:
                    available = False
            if not available:
                permission_svc = AdxPermissionService(kusto_client=kusto_client, state=state.get("services"))
                existing_permissions = permission_svc.get_all()
                existing_ids = [ent.get("principal_id") for ent in existing_permissions]
                spec_permissions: list = adx_section["database"].get("permissions", [])
                if len(spec_permissions):
                    ids = [i.get("principal_id") for i in spec_permissions]
                    for g in spec_permissions:
                        if g.get("principal_id") in existing_ids:
                            deleted = permission_svc.delete(g.get("principal_id"), force_validation=True)
                            if deleted:
                                permission_svc.set(
                                    principal_id=g.get("principal_id"),
                                    principal_type=g.get("type"),
                                    role=g.get("role"),
                                    tenant_id=g.get("tenant_id", env.tenant_id),
                                )
                        if g.get("principal_id") not in existing_ids:
                            permission_svc.set(
                                principal_id=g.get("principal_id"),
                                principal_type=g.get("type"),
                                role=g.get("role"),
                                tenant_id=g.get("tenant_id", env.tenant_id),
                            )
                    for s in existing_ids:
                        if s not in ids:
                            if s != state["services"]["babylon"]["client_id"]:
                                permission_svc.delete(s, force_validation=True)
            if ok:
                scripts_svc = AdxScriptService(kusto_client=kusto_client, state=state.get("services"))
                script_list = scripts_svc.get_all()
                scripts_spec: list[dict] = adx_section.get("database").get("scripts", [])
                database_uri = adx_section.get("database").get("uri", "")
                if len(scripts_spec):
                    for s in scripts_spec:
                        t = list(filter(lambda x: s.get("id") in str(x.get("id")), script_list))
                        if not len(t):
                            name = s.get("name")
                            path_end = s.get("path")
                            path_abs = pathlib.Path(deploy_dir) / f"{path_end}/{name}"
                            scripts_svc.execute_query(
                                script_file=path_abs.absolute(),
                                database_uri=database_uri,
                            )
        if eventhub_section:
            kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
            arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
            iam_client = AuthorizationManagementClient(credential=azure_credential, subscription_id=subscription_id)
            adx_svc = ArmService(arm_client=arm_client, state=state.get("services"))
            to_create = eventhub_section.get("create", True)
            if to_create:
                deployment_name = f"{organization_id}-evn-{workspace_key}"
                adx_svc.run(deployment_name=deployment_name, file="eventhub_deploy.json")
            arm_svc = AzureIamService(iam_client=iam_client, state=state.get("services"))
            principal_id = state["services"]["adx"]["cluster_principal_id"]
            resource_type = "Microsoft.EventHub/Namespaces"
            resource_name = f"{organization_id}-{workspace_key}"
            role_id = state["services"]["azure"]["eventhub_built_data_receiver"]
            arm_svc.set(
                principal_id=principal_id,
                resource_name=resource_name,
                resource_type=resource_type,
                role_id=role_id,
            )
            principal_id = state["services"]["platform"]["principal_id"]
            resource_type = "Microsoft.EventHub/Namespaces"
            resource_name = f"{organization_id}-{workspace_key}"
            role_id = state["services"]["azure"]["eventhub_built_data_sender"]
            arm_svc.set(
                principal_id=principal_id,
                resource_name=resource_name,
                resource_type=resource_type,
                role_id=role_id,
            )
            principal_id = state["services"]["babylon"]["principal_id"]
            resource_type = "Microsoft.EventHub/Namespaces"
            resource_name = f"{organization_id}-{workspace_key}"
            role_id = state["services"]["azure"]["eventhub_built_data_sender"]
            arm_svc.set(
                principal_id=principal_id,
                resource_name=resource_name,
                resource_type=resource_type,
                role_id=role_id,
            )
            consumers = eventhub_section.get("consumers", [])
            ent_accepted = [
                "ProbesMeasures",
                "ScenarioMetadata",
                "ScenarioRun",
                "ScenarioRunMetadata",
            ]
            if len(consumers):
                service_event = AdxConsumerService(state=state.get("services"))
                for ent in ent_accepted:
                    spec_listing = [
                        k.get("displayName") for k in list(filter(lambda x: x.get("entity") == ent, consumers))
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
                service_conn = AdxConnectionService(kusto_client=kusto_client, state=state.get("services"))
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
                            to_delete = list(
                                filter(
                                    lambda x: x.get("table_name") == hc.get("table"),
                                    existing_connectors,
                                ))
                            if to_delete:
                                connection_name = to_delete[-1]["name"].split("/")[-1]
                                service_conn.delete(database_name=db, connection_name=connection_name)
        run_scripts = sidecars.get("run_scripts")
        if run_scripts:
            data = run_scripts.get("post_deploy.sh", "")
            if data:
                print(data)
                os.system(data)
        if not workspace.get("id"):
            logger.error("workspace id not found")
            sys.exit(1)

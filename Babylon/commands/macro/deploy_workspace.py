import os
import sys
import json
import click
import pathlib

from logging import getLogger
from Babylon.utils.environment import Environment
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import (
    AzurePowerBIReportService, )
from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import (
    AzurePowerBIDatasetService, )
from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import (
    AzurePowerBIWorkspaceService, )
from Babylon.commands.powerbi.dataset.services.powerbi_params_svc import (
    AzurePowerBIParamsService, )
from Babylon.utils.credentials import (
    get_default_powerbi_token,
    get_keycloak_token,
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
            logger.error(f"Missing 'organization_id' in metadata -> selector field : {metadata.get('selector')}")
            sys.exit(1)
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload")
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    keycloak_token = get_keycloak_token()
    workspace_svc = WorkspaceService(keycloak_token=keycloak_token, spec=spec, state=state.get("services"))
    if not state["services"]["api"]["workspace_id"]:
        logger.info("[api] Creating workspace")
        response = workspace_svc.create()
        if not response:
            sys.exit(1)
        workspace = response.json()
        logger.info(json.dumps(workspace, indent=2))
        logger.info(f"[api] Workspace {[workspace.get('id')]} successfully created")
        state["services"]["api"]["workspace_id"] = workspace.get("id")
    else:
        logger.info(f"[api] Updating workspace {[state['services']['api']['workspace_id']]}")
        response = workspace_svc.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = workspace_svc.update_security(old_security=old_security)
        response_json["security"] = security_spec
        workspace = response_json
        logger.info(json.dumps(workspace, indent=2))
        logger.info(f"[api] Workspace {[workspace['id']]} successfully updated")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)

    # TODO: Update sidecars to support Superset in the future.
    # For now, keeping the same implementation as Power BI until we fully understand how it works.
    # Once clarified, we will modify this part to work with Superset.
    sidecars = content.get("spec").get("sidecars", None)
    if (content.get("spec").get("payload") is not None
            and content.get("spec").get("payload").get("webApp") is not None):
        workspaceCharts = (content.get("spec").get("payload").get("webApp").get("options").get("charts") or None)
    else:
        workspaceCharts = None
    if sidecars and not payload_only:
        superset_section = sidecars.get("superset", {})
        if superset_section:
            workspace_powerbi = superset_section.get("workspace", {})
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
        if workspaceCharts is not None and superset_section:
            content.get("spec").get("payload").get("webApp").get("options").get(
                "charts")["workspaceId"] = state["services"]["powerbi"]["workspace.id"]
            logger.info(
                f"[powerbi] updating workspace {state['services']['api']['workspace_id']} with all powerbi reports")
            payloadUpdated: dict = content.get("spec").get("payload")
            specUpdated = dict()
            specUpdated["payload"] = json.dumps(payloadUpdated, indent=2, ensure_ascii=True)
            workspace_svc.update_with_payload(specUpdated)
        run_scripts = sidecars.get("run_scripts")
        if run_scripts:
            data = run_scripts.get("post_deploy.sh", "")
            if data:
                print(data)
                os.system(data)
        if not workspace.get("id"):
            logger.error("workspace id not found")
            sys.exit(1)

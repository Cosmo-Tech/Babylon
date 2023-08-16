import os
import logging
import pathlib
import polling2
import requests
import jmespath

from typing import Any
from click import Choice, command
from click import Path
from click import option
from Babylon.utils.decorators import inject_context_with_resource, timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token
from ruamel.yaml import YAML

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@pass_powerbi_token()
@option("-f",
        "--file",
        "pbix_filename",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        required=True)
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--override", "override", is_flag=True, help="override reports in case of name conflict")
@option("-s", "--select", "select", is_flag=True, default=True, help="Select this new report in configuration")
@option("-n", "--name", "report_name", type=QueryType())
@option("-t", "--type", "report_type", type=Choice(["scenario_view", "dashboard_view"]), required=True)
@inject_context_with_resource({"powerbi": ['workspace']})
def upload(
    context: Any,
    powerbi_token: str,
    pbix_filename: pathlib.Path,
    workspace_id: str,
    report_name: str,
    report_type: str,
    override: bool = False,
    select: bool = False,
) -> CommandResponse:
    """
    Publish the given pbxi file to the PowerBI workspace
    """

    workspace_id = workspace_id or context["powerbi_workspace"]['id']
    name = os.path.splitext(pbix_filename)[0]
    header = {"Content-Type": "multipart/form-data", "Authorization": f"Bearer {powerbi_token}"}
    name_conflict = "CreateOrOverwrite" if override else "Abort"
    route = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
             f"/imports?datasetDisplayName={name}&nameConflict={name_conflict}")
    session = requests.Session()
    with open(pbix_filename, "rb") as _f:
        try:
            response = session.post(url=route, headers=header, files={"file": _f})
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return CommandResponse.fail()
        if response.status_code >= 300:
            logger.error(f"Request failed ({response.status_code}): {response.text}")
            return CommandResponse.fail()
    import_data = response.json()
    # Wait for import end

    route = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports/{import_data.get('id')}"
    output_data = {}
    logger.info(f"Waiting for import of file {pbix_filename} to end")
    handler = polling2.poll(lambda: oauth_request(route, powerbi_token),
                            check_success=is_correct_response_app,
                            step=1,
                            timeout=60)

    output_data = handler.json()
    report_name = report_name or output_data['reports'][0]['name']
    if select:
        yaml_loader = YAML()
        data_file = env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.powerbi.yaml"
        if data_file.exists():
            yaml_file = data_file

        with yaml_file.open(mode='r') as _f:
            data = yaml_loader.load(_f)
        dashboard_view = data[env.context_id][report_type]
        if dashboard_view is None:
            dashboard_view = []
        idx = None
        test_match = jmespath.search(f"[?contains(reportId, '{output_data['reports'][0]['id']}')]", dashboard_view)
        if test_match:
            idx = dashboard_view.index(test_match[0])

        if idx is not None:
            report_data = data[env.context_id][report_type][idx]
            data[env.context_id][report_type][idx] = report_data
            dashboard_view = data[env.context_id][report_type]
        else:
            new_report = {
                "reportId": output_data['reports'][0]['id'],
                "title": {
                    "en": report_name,
                    "fr": report_name,
                },
                "settings": {
                    "navContentPaneEnabled": True,
                    "panes": {
                        "filters": {
                            "expanded": report_type == "scenario_view",
                            "visible": True
                        }
                    }
                },
                "pageName": None
            }
            dashboard_view.append(new_report)

        data[env.context_id][report_type] = dashboard_view
        with data_file.open(mode='w+') as _f:
            yaml_loader.dump(data, data_file)
        logger.info("Updated configuration variable powerbi_report_id")

    logger.info("Successfully imported")
    return CommandResponse.success(output_data, verbose=True)


def is_correct_response_app(response):
    output_data = response.json()
    if output_data.get("importState") == "Succeeded":
        return output_data

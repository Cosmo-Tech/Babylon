import os
import polling2
import logging

from pathlib import Path

import jmespath
import requests
import yaml
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.macro import Macro
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzurePowerBIReportService:

    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def delete(self, workspace_id: str, report_id: str, force_validation: bool):
        report_id = report_id or self.state["powerbi"]["workspace"]["report_id"]
        if not force_validation and not confirm_deletion("report", report_id):
            return CommandResponse.fail()
        urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
        response = oauth_request(url=urls_reports, access_token=self.powerbi_token, type="DELETE")
        if response is None:
            return CommandResponse.fail()
        return response

    def download_all(self, workspace_id: str, output_folder: Path):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        logger.info(f"Downloading reports from workspace {workspace_id}...")
        if not output_folder.exists():
            output_folder.mkdir()
        m = (Macro("PowerBI download all", "powerbi").step(
            [
                "powerbi",
                "report",
                "get-all",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
                "--workspace-id",
                workspace_id,
            ],
            store_at="reports",
        ).iterate(
            "datastore.reports.data",
            [
                "powerbi",
                "report",
                "download",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
                "--workspace-id",
                workspace_id,
                "%datastore%item.id",
                "--override",
                str(output_folder),
            ],
        ))
        reports = m.env.get_data(["reports", "data"])
        logger.info("Successfully saved the following reports:")
        logger.info("\n".join(f"- {output_folder}/{report['name']}.pbix" for report in reports))
        return m

    def download(self, workspace_id: str, report_id: str, output_folder: Path):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
        response = oauth_request(url_report, self.powerbi_token)
        if response is None:
            return CommandResponse.fail()
        output_path = Path(response.headers.get("X-PowerBI-FileName"))
        if output_folder:
            output_path = output_folder / output_path
        with open(output_path, "wb") as file:
            file.write(response.content)
        logger.info(f"Report {report_id} was saved as {output_path}")
        return output_path

    def get_all(self, workspace_id: str, filter: bool):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        urls_reports = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports")
        response = oauth_request(urls_reports, self.powerbi_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json().get("value")
        if filter:
            output_data = jmespath.search(filter, output_data)

    def get(self, workspace_id: str, report_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
        response = oauth_request(urls_reports, self.powerbi_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        return output_data

    def pages(self, workspace_id: str, report_id: str, report_type: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/pages"
        response = oauth_request(urls_reports, self.powerbi_token)
        if response is None:
            logger.info("Report id not found")
            return CommandResponse.fail()
        output_data = response.json()
        pagesnames = jmespath.search("value[?order==`0`]", output_data)
        pagesname = pagesnames[0] if len(pagesnames) else "ReportSection"
        data_file = (env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.powerbi.yaml")
        if not data_file.exists():
            logger.info(f"Config file {env.context_id}.{env.environ_id}.powerbi.yaml not found")
            return CommandResponse.fail()
        data = yaml.load(data_file.open("r"), Loader=yaml.SafeLoader)
        _view = data[env.context_id][report_type]
        test_match = jmespath.search(f"[?contains(reportId, '{report_id}')]", _view)

        if len(test_match):
            idx = _view.index(test_match[0])
        if pagesname:
            _view[idx]["pageName"] = {
                "en": f"{pagesname['name']}",
                "fr": f"{pagesname['name']}",
            }
        data[env.context_id][report_type][idx] = _view[idx]
        data_file.write_bytes(data=yaml.dump(data).encode("utf-8"))

    def upload(
        self,
        workspace_id: str,
        pbix_filename: Path,
        report_name: str,
        report_type: str,
        override: bool,
    ):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        name = os.path.splitext(pbix_filename)[0]
        header = {
            "Content-Type": "multipart/form-data",
            "Authorization": f"Bearer {self.powerbi_token}",
        }
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
        handler = polling2.poll(
            lambda: oauth_request(route, self.powerbi_token),
            check_success=is_correct_response_app,
            step=1,
            timeout=60,
        )
        output_data = handler.json()
        report_name = report_name or output_data["reports"][0]["name"]
        data_file = (env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.powerbi.yaml")
        if data_file.exists():
            data = yaml.load(_f, Loader=yaml.SafeLoader)
        dashboard_view = data[env.context_id][report_type]
        if dashboard_view is None:
            dashboard_view = []
        idx = None
        test_match = jmespath.search(
            f"[?contains(reportId, '{output_data['reports'][0]['id']}')]",
            dashboard_view,
        )
        if test_match:
            idx = dashboard_view.index(test_match[0])
        if idx is not None:
            report_data = data[env.context_id][report_type][idx]
            data[env.context_id][report_type][idx] = report_data
            dashboard_view = data[env.context_id][report_type]
        else:
            new_report = {
                "reportId": output_data["reports"][0]["id"],
                "title": {
                    "en": report_name,
                    "fr": report_name,
                },
                "settings": {
                    "navContentPaneEnabled": True,
                    "panes": {
                        "filters": {
                            "expanded": report_type == "scenario_view",
                            "visible": True,
                        }
                    },
                },
                "pageName": None,
            }
            dashboard_view.append(new_report)
        data[env.context_id][report_type] = dashboard_view
        data_file.write_bytes(yaml.dump(data).encode("utf-8"))
        logger.info("Updated configuration variable powerbi_report_id")
        logger.info("Successfully imported")
        return CommandResponse.success(output_data, verbose=True)


def is_correct_response_app(response):
    output_data = response.json()
    if output_data.get("importState") == "Succeeded":
        return output_data

import logging
import os
from pathlib import Path

import polling2
import requests

from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")
env = Environment()


class AzurePowerBIReportService:
    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def delete(self, workspace_id: str, report_id: str, force_validation: bool):
        report_id = report_id or self.state["powerbi"]["workspace"]["report_id"]
        if not force_validation and not confirm_deletion("report", report_id):
            return None
        urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
        response = oauth_request(url=urls_reports, access_token=self.powerbi_token, type="DELETE")
        if response is None:
            logger.error(f"[powerbi] failed to delete report with id : {report_id} ")
            return None
        return response

    def download_all(self, workspace_id: str, output_folder: Path):
        logger.info("[powerbi] download all reports")
        if not output_folder.exists():
            output_folder.mkdir()
        reports = self.get_all(workspace_id=workspace_id)
        for r in reports:
            self.download(workspace_id=workspace_id, report_id=r.get("id"), output_folder=output_folder)
            logger.info("[powerbi] successfully saved the following reports:")
        logger.info("\n".join(f"- {output_folder}/{report['name']}.pbix" for report in reports))

    def download(self, workspace_id: str, report_id: str, output_folder: Path):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_report = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
        response = oauth_request(url_report, self.powerbi_token)
        if response is None:
            logger.error(f"[powerbi] failed to export report with id : {report_id} ")
            return None
        output_path = Path(response.headers.get("X-PowerBI-FileName"))
        if output_folder:
            output_path = output_folder / output_path
        with open(output_path, "wb") as file:
            file.write(response.content)
        logger.info(f"[powerbi] report {report_id} was saved as {output_path}")
        return output_path

    def get_all(self, workspace_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
        response = oauth_request(urls_reports, self.powerbi_token)
        if response is None:
            logger.error("[powerbi] failed to get all reports")
            return None
        return response

    def get(self, workspace_id: str, report_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
        response = oauth_request(urls_reports, self.powerbi_token)
        if response is None:
            logger.error("[powerbi] failed to get report by report_id")
            return None
        output_data = response.json()
        return output_data

    def pages(self, workspace_id: str, report_id: str, report_type: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/pages"
        response = oauth_request(urls_reports, self.powerbi_token)
        if response is None:
            logger.info("[powerbi] report id not found")
            return None
        output_data = response.json()
        pagesname = output_data[0] if len(output_data) else "ReportSection"
        obj = {"en": f"{pagesname['name']}", "fr": f"{pagesname['name']}"}
        return obj

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
        route = (
            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports?datasetDisplayName={name}&nameConflict={name_conflict}"
        )
        session = requests.Session()
        with open(pbix_filename, "rb") as _f:
            try:
                response = session.post(url=route, headers=header, files={"file": _f})
            except Exception as e:
                logger.error(f"[powerbi] request failed: {e}")
                return None
            if response.status_code >= 300:
                logger.error(f"Request failed ({response.status_code}): {response.text}")
                return None
        import_data = response.json()
        # Wait for import end

        route = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports/{import_data.get('id')}"
        output_data = {}
        logger.info(f"[powerbi] waiting for import of file {pbix_filename} to end")
        handler = polling2.poll(
            lambda: oauth_request(route, self.powerbi_token),
            check_success=is_correct_response_app,
            step=1,
            timeout=60,
        )
        output_data = handler.json()
        report_name = report_name or output_data["reports"][0]["name"]
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
        return output_data, new_report


def is_correct_response_app(response):
    output_data = response.json()
    if output_data.get("importState") == "Succeeded":
        return output_data

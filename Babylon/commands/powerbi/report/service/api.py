import os
import logging
import jmespath
import requests
import polling2

from pathlib import Path
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion

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
        logger.info('download all reports')
        if not output_folder.exists():
            output_folder.mkdir()
        reports = self.get_all(workspace_id=workspace_id)
        for r in reports:
            self.download(workspace_id=workspace_id, report_id=r.get('id'), output_folder=output_folder)
            logger.info("Successfully saved the following reports:")
        logger.info("\n".join(f"- {output_folder}/{report['name']}.pbix" for report in reports))

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

    def get_all(self, workspace_id: str, filter: str = ""):
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
        return new_report


def is_correct_response_app(response):
    output_data = response.json()
    if output_data.get("importState") == "Succeeded":
        return output_data

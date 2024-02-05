import logging

from pathlib import Path
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
        response = oauth_request(
            url=urls_reports, access_token=self.powerbi_token, type="DELETE"
        )
        if response is None:
            return CommandResponse.fail()
        return response

    def download_all(self, workspace_id: str, output_folder: Path):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        logger.info(f"Downloading reports from workspace {workspace_id}...")
        if not output_folder.exists():
            output_folder.mkdir()
        m = (
            Macro("PowerBI download all", "powerbi")
            .step(
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
            )
            .iterate(
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
            )
        )
        reports = m.env.get_data(["reports", "data"])
        logger.info("Successfully saved the following reports:")
        logger.info(
            "\n".join(f"- {output_folder}/{report['name']}.pbix" for report in reports)
        )
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

    def get_all(self):
        pass

    def get(self):
        pass

    def pages(self):
        pass

    def upload(self):
        pass

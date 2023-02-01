import logging
import pathlib
from typing import Iterable
from typing import Tuple

from click import Path
from click import argument
from click import command
from click import option

from ....utils.command_helper import run_command
from ....utils.response import CommandResponse
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@argument("workspace_name", type=QueryType())
@option("--report-folder",
        "-f",
        "report_folder",
        type=Path(exists=True, dir_okay=True, file_okay=False, readable=True, path_type=pathlib.Path),
        default="./powerbi-reports")
@option("--report-parameter", "-p", "report_parameters", type=(QueryType(), QueryType()), multiple=True)
def deploy_workspace(workspace_name: str, report_folder: pathlib.Path, report_parameters: Iterable[Tuple[str, str]]):
    """Macro command allowing full deployment of a power bi workspace

    Require a local folder named `powerbi-reports` and will initialize a full workspace with the given reports"""
    r_create_ws: CommandResponse = run_command(f"powerbi workspace create -s {workspace_name}".split())
    if r_create_ws.status_code == r_create_ws.STATUS_ERROR:
        logger.error("Error while creating the workspace")
        return
    workspace_id = r_create_ws.data['id']
    logger.info(f"Created workspace {workspace_name} - {workspace_id}")
    logger.info("Uploading reports")
    for report_path in report_folder.glob("*.pbix"):
        logger.info("")
        logger.info(f"Uploading \"{report_path}\"")
        r_upload_report: CommandResponse = run_command(f"powerbi report upload -w {workspace_id}".split() +
                                                       [str(report_path)])
        if r_upload_report.status_code == r_create_ws.STATUS_ERROR:
            logger.error(f"Error while updating the report \"{report_path}\"")
            continue
        reports = r_upload_report.data.get('reports', [])
        for report in reports:
            logger.info(f"Uploaded report \"{report.get('name')}\" ({report.get('id')})")
        datasets = r_upload_report.data.get('datasets', [])
        for dataset in datasets:
            dataset_id = dataset.get('id')
            if report_parameters:
                logger.info(f"Applying parameters to dataset \"{dataset.get('name')}\" ({dataset_id})")
                for k, v in report_parameters:
                    r_update_parameter: CommandResponse = run_command(
                        f"powerbi dataset parameters update {dataset_id} -w {workspace_id} -p {k} {v}".split())
                    if r_update_parameter.status_code == r_create_ws.STATUS_ERROR:
                        logger.error(f"Error while setting the parameter {k}")
                        continue
            else:
                logger.warning("No parameter to apply")
            logger.info(f"Updating credentials for dataset \"{dataset.get('name')}\" ({dataset_id})")
            r_update_credentials: CommandResponse = run_command(
                f"powerbi dataset update-credentials {dataset_id} -w {workspace_id}".split())
            if r_update_credentials.status_code == r_create_ws.STATUS_ERROR:
                logger.error(f"Error while updating credentials for dataset  \"{dataset.get('name')}\" ({dataset_id})")
                continue
    logger.info(f"DONE - Workspace deployment of \"{workspace_name}\" ({workspace_id})")

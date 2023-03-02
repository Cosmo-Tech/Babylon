import logging
import pathlib
from typing import Iterable
from typing import Tuple

from click import Path
from click import argument
from click import command
from click import option

from ....utils.typing import QueryType
from ....utils.macro import Macro

logger = logging.getLogger("Babylon")


@command()
@argument("workspace_name", type=QueryType())
@option("--report-folder",
        "-f",
        "report_folder",
        type=Path(exists=True, dir_okay=True, file_okay=False, readable=True, path_type=pathlib.Path),
        default="./powerbi-reports",
        help="Override folder containing your .pbix files")
@option("--report-parameter",
        "-p",
        "report_parameters",
        type=(QueryType(), QueryType()),
        multiple=True,
        help="Add a combination <Key Value> that will be sent as parameter to all your datasets")
def deploy_workspace(workspace_name: str, report_folder: pathlib.Path, report_parameters: Iterable[Tuple[str, str]]):
    """Macro command allowing full deployment of a power bi workspace

    Require a local folder named `powerbi-reports` and will initialize a full workspace with the given reports"""
    report_params = " ".join([f"-p {param[0]} {param[1]}" for param in report_parameters])
    Macro("powerbi workspace deploy") \
        .step(["powerbi", "workspace", "create", "-s", workspace_name], store_at="workspace") \
        .step(
            ["powerbi", "report", "upload", "-w", "%datastore%workspace.data.id", report_folder], store_at="reports") \
        .iterate(["powerbi", "dataset", "parameters", "update", "-w", "%datastore%workspace.data.id", report_params],
                 iterate_on="%datastore%reports.data.datasets") \
        .dump("powerbi_deploy_workspace.json")

    # for report_path in report_folder.glob("*.pbix"):
    #     reports = r_upload_report.data.get('reports', [])
    #     for report in reports:
    #         logger.info(f"Uploaded report \"{report.get('name')}\" ({report.get('id')})")
    #     datasets = r_upload_report.data.get('datasets', [])
    #     for dataset in datasets:
    #         dataset_id = dataset.get('id')
    #         if report_parameters:
    #             logger.info(f"Applying parameters to dataset \"{dataset.get('name')}\" ({dataset_id})")
    #             for k, v in report_parameters:
    #                 r_update_parameter: CommandResponse = run_command(
    #                     f"powerbi dataset parameters update {dataset_id} -w {workspace_id} -p {k} {v}".split())
    #                 if r_update_parameter.status_code == r_create_ws.STATUS_ERROR:
    #                     logger.error(f"Error while setting the parameter {k}")
    #                     continue
    #         else:
    #             logger.warning("No parameter to apply")
    #         logger.info(f"Updating credentials for dataset \"{dataset.get('name')}\" ({dataset_id})")
    #         r_update_credentials: CommandResponse = run_command(
    #             f"powerbi dataset update-credentials {dataset_id} -w {workspace_id}".split())
    #         if r_update_credentials.status_code == r_create_ws.STATUS_ERROR:
    #             logger.error(f"Error while updating credentials for dataset  \"{dataset.get('name')}\" ({dataset_id})")
    #             continue
    # logger.info(f"DONE - Workspace deployment of \"{workspace_name}\" ({workspace_id})")

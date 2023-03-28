import logging
import pathlib
from typing import Iterable
from typing import Tuple
from typing import Optional

from click import Path
from click import argument
from click import command
from click import option

from ...utils.typing import QueryType
from ...utils.macro import Macro

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
def deploy_workspace(workspace_name: str,
                     report_folder: pathlib.Path,
                     report_parameters: Optional[Iterable[Tuple[str, str]]] = None):
    """
    Macro command allowing full deployment of a power bi workspac
    Require a local folder named `powerbi-reports` and will initialize a full workspace with the given reports
    Won't run powerbi workspace creation if it's already existing
    """
    report_params = " ".join([f"-p {param[0]} {param[1]}" for param in report_parameters]) if report_parameters else ""

    macro = Macro("powerbi workspace deploy") \
        .step(["powerbi", "workspace", "get", "-n", workspace_name], store_at="workspace", is_required=False)
    macro.step(["powerbi", "workspace", "create", workspace_name],
               store_at="workspace",
               run_if=not macro.env.get_data(["workspace", "data"]))
    for report_path in report_folder.glob("*.pbix"):
        macro.step(["powerbi", "report", "upload", "-w", "%datastore%workspace.data.id",
                    str(report_path)],
                   store_at="report")
        for dataset in macro.env.convert_data_query("%datastore%report.data.datasets") or []:
            macro.step(["powerbi", "dataset", "parameters", "update", "-w", "%datastore%workspace.data.id",
                       dataset["id"], *report_params.split(" ")], run_if=report_params != "") \
                .step(["powerbi", "dataset", "update-credentials", "-w", "%datastore%workspace.data.id", dataset["id"]])
    macro.dump("powerbi_workspace_deploy.json")

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
        default="./POWERBI",
        help="Override folder containing your .pbix files")
@option("--report-parameter",
        "-p",
        "report_parameters",
        type=(QueryType(), QueryType()),
        multiple=True,
        help="Add a combination <Key Value> that will be sent as parameter to all your datasets")
@option("--override", "override", is_flag=True, help="override reports in case of name conflict ?")
def deploy_workspace(workspace_name: str,
                     report_folder: pathlib.Path,
                     report_parameters: Optional[Iterable[Tuple[str, str]]] = None,
                     override: bool = False):
    """
    Macro command allowing full deployment of a powerBI workspace  
    Requires a local folder named `POWERBI` and will initialize a full workspace with the given reports  
    Won't run powerbi workspace creation if it's already existing  
    """
    report_params = " ".join([f"-p {param[0]} {param[1]}" for param in report_parameters]) if report_parameters else ""
    macro = Macro("powerbi workspace deploy") \
        .step(["powerbi", "workspace", "get", "-n", workspace_name], store_at="workspace", is_required=False)
    macro.step(["powerbi", "workspace", "create", workspace_name, "-s"], store_at="workspace", run_if=not macro.env.get_data(["workspace", "data"]))
    upload_cmd = ["powerbi", "report", "upload"]
    if override:
        upload_cmd.append("--override")
    for report_path in report_folder.glob("*.pbix"):
        macro.step([*upload_cmd, str(report_path), "-s"], store_at="report")
        for dataset in macro.env.convert_data_query("%datastore%report.data.datasets") or []:
            macro.step(["powerbi", "dataset", "take-over", dataset["id"]]) \
                .step(["powerbi", "dataset", "parameters", "update", dataset["id"], *report_params.split(" ")], run_if=report_params != "") \
                .step(["powerbi", "dataset", "update-credentials", dataset["id"]])
    macro.dump("powerbi_workspace_deploy.json")

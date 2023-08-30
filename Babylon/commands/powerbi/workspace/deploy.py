import logging
import pathlib

from typing import Any, Iterable
from typing import Tuple
from typing import Optional
from click import Choice, Path
from click import argument
from click import command
from click import option
from Babylon.utils.checkers import check_email, check_encoding_key
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.typing import QueryType
from Babylon.utils.macro import Macro

logger = logging.getLogger("Babylon")


@command()
@option("-f",
        "--folder",
        "report_folder",
        type=Path(exists=True, dir_okay=True, file_okay=False, readable=True, path_type=pathlib.Path),
        required=True,
        help="Override folder containing your .pbix files")
@option("--parameter",
        "-p",
        "report_parameters",
        type=(QueryType(), QueryType()),
        multiple=True,
        help="Add a combination <Key Value> that will be sent as parameter to all your datasets")
@option("--override", "override", is_flag=True, help="override reports in case of name conflict ?")
@option("-t", "--type", "report_type", type=Choice(["scenario_view", "dashboard_view"]), required=True)
@argument("workspace_name", type=QueryType())
@inject_context_with_resource({"adx": ['database_name', 'cluster_uri'], "azure": ['email']})
def deploy(context: Any,
           workspace_name: str,
           report_folder: pathlib.Path,
           report_type: str,
           override: bool,
           report_parameters: Optional[Iterable[Tuple[str, str]]] = None):
    """
    Macro command allowing full deployment of a powerBI workspace  
    Requires a local folder named `POWERBI` and will initialize a full workspace with the given reports  
    Won't run powerbi workspace creation if it's already existing  
    """
    email = context['azure_email']
    check_email(email)
    check_encoding_key()

    adx_cluster = context['adx_cluster_uri']
    adx_database = context['adx_database_name']
    report_params = " ".join([f"-p {param[0]} {param[1]}" for param in report_parameters]) if report_parameters else ""
    if not report_params:
        report_params = "".join(f"-p ADX_CLUSTER {adx_cluster} -p ADX_DATABASE {adx_database}")

    macro = Macro("powerbi workspace deploy").step(["powerbi", "workspace", "get", "-n", workspace_name],
                                                   store_at="workspace")

    if not macro.env.get_data_from_store(["workspace"]):
        macro.step(["powerbi", "workspace", "create", workspace_name], store_at="workspace")

    macro = macro.step(["powerbi", "workspace", "user", "get-all", "--filter", f"[?emailAddress=='{email}']"],
                       store_at="user")

    user = macro.env.get_data_from_store(["user"])
    if not user:
        macro.step(["powerbi", "workspace", "user", "add", email, "User", "Admin"])

    upload_cmd = ["powerbi", "report", "upload"]
    if override:
        upload_cmd.append("--override")
    upload_cmd = upload_cmd + ["-t", report_type, "-f"]
    for report_path in report_folder.glob("*.pbix"):
        cmd_line = [*upload_cmd, str(report_path)]
        macro = macro.step(cmd_line, store_at="report")
        report = macro.env.get_data_from_store(["report"])
        macro = macro.step(["powerbi", "report", "pages", "-t", report_type, report["id"]])
        datasets = report["datasets"]
        for dataset in datasets:
            macro.step(["powerbi", "dataset", "take-over", dataset["id"], "-e", email]).step([
                "powerbi", "dataset", "parameters", "update", dataset["id"], "-e", email, *report_params.split(" ")
            ]).step(["powerbi", "dataset", "update-credentials", dataset["id"], "-e", email])

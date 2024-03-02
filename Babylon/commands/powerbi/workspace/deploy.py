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
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.environment import Environment

from Babylon.utils.macro import Macro

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@option("--folder",
        "report_folder",
        type=Path(exists=True, dir_okay=True, file_okay=False, readable=True, path_type=pathlib.Path),
        required=True,
        help="Override folder containing your .pbix files")
@option("--parameter",
        "report_parameters",
        type=(str, str),
        multiple=True,
        help="Add a combination <Key Value> that will be sent as parameter to all your datasets")
@option("--override", "override", is_flag=True, help="override reports in case of name conflict ?")
@option("--type", "report_type", type=Choice(["scenario_view", "dashboard_view"]), required=True, help="Report type")
@argument("workspace_name", type=str)
@retrieve_state
def deploy(state: Any,
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
    email = state['azure_email']
    check_email(email)
    check_encoding_key()

    adx_cluster = state['adx_cluster_uri']
    adx_database = state['adx_database_name']
    report_params = " ".join([f"--parameter {param[0]} {param[1]}"
                              for param in report_parameters]) if report_parameters else ""
    if not report_params:
        report_params = "".join(f"--parameter ADX_cluster {adx_cluster} --parameter ADX_database {adx_database}")

    macro = Macro("powerbi workspace deploy").step(
        ["powerbi", "workspace", "get", "-c", env.context_id, "-p", env.environ_id, "--name", workspace_name],
        store_at="workspace")
    if not macro.env.get_data_from_store(["workspace"]):
        macro.step(["powerbi", "workspace", "create", workspace_name, "-c", env.context_id, "-p", env.environ_id],
                   store_at="workspace")

    macro = macro.step([
        "powerbi", "workspace", "user", "get-all", "-c", env.context_id, "-p", env.environ_id, "--filter",
        f"[?emailAddress=='{email}']"
    ],
                       store_at="user")

    user = macro.env.get_data_from_store(["user"])
    if not user:
        macro.step(
            ["powerbi", "workspace", "user", "add", "-c", env.context_id, "-p", env.environ_id, email, "User", "Admin"])

    upload_cmd = ["powerbi", "report", "upload", "-c", env.context_id, "-p", env.environ_id]
    if override:
        upload_cmd.append("--override")
    upload_cmd = upload_cmd + ["--type", report_type, "--file"]
    for report_path in report_folder.glob("*.pbix"):
        cmd_line = [*upload_cmd, str(report_path)]
        macro = macro.step(cmd_line, store_at="report")
        report = macro.env.get_data_from_store(["report"])
        macro = macro.step([
            "powerbi", "report", "pages", "-c", env.context_id, "-p", env.environ_id, "--report-type", report_type,
            report["reports"][0]["id"]
        ])
        datasets = report["datasets"]
        for dataset in datasets:
            macro.step([
                "powerbi", "dataset", "take-over", "-c", env.context_id, "-p", env.environ_id, dataset["id"], "--email",
                email
            ]).step([
                "powerbi", "dataset", "parameters", "update", "-c", env.context_id, "-p", env.environ_id, dataset["id"],
                "--email", email, *report_params.split(" ")
            ]).step([
                "powerbi", "dataset", "update-credentials", "-c", env.context_id, "-p", env.environ_id, dataset["id"],
                "--email", email
            ])

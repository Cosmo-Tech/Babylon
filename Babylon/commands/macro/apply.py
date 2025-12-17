import os
import pathlib
from logging import getLogger
from typing import Iterable

from click import Path, argument, command, echo, option, style
from yaml import safe_dump, safe_load

from Babylon.commands.macro.deploy_organization import deploy_organization
from Babylon.commands.macro.deploy_solution import deploy_solution
from Babylon.commands.macro.deploy_workspace import deploy_workspace
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def load_resources_from_files(files_to_deploy: list[pathlib.Path]) -> tuple[list, list, list]:
    resources = []
    for f in files_to_deploy:
        resource = {}
        with open(f) as input_file:
            content = input_file.read()
            escaped_content = content.replace("{{", "${").replace("}}", "}")
            yaml_data = safe_load(escaped_content)
            resource["kind"] = yaml_data.get("kind")
            resource["namespace"] = safe_dump(yaml_data.get("namespace"))
            resource["content"] = escaped_content
            resources.append(resource)
    organizations = list(filter(lambda x: x.get("kind") == "Organization", resources))
    solutions = list(filter(lambda x: x.get("kind") == "Solution", resources))
    workspaces = list(filter(lambda x: x.get("kind") == "Workspace", resources))
    return (organizations, solutions, workspaces)


def deploy_objects(objects: list, object_type: str):
    for o in objects:
        content = o.get("content")
        namespace = o.get("namespace")
        if object_type == "organization":
            deploy_organization(namespace=namespace, file_content=content)
        elif object_type == "solution":
            deploy_solution(namespace=namespace, file_content=content)
        elif object_type == "workspace":
            deploy_workspace(namespace=namespace, file_content=content)


@command()
@injectcontext()
@argument("deploy_dir", type=Path(dir_okay=True, exists=True))
@option(
    "--var-file",
    "variables_files",
    type=Path(file_okay=True, exists=True),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)
@option("--organization", is_flag=True, help="Deploy or update an organization.")
@option("--solution", is_flag=True, help="Deploy or update a solution.")
@option("--workspace", is_flag=True, help="Deploy or update a workspace.")
def apply(
    deploy_dir: pathlib.Path,
    organization: bool,
    solution: bool,
    workspace: bool,
    variables_files: Iterable[pathlib.Path],
):
    """Macro Apply"""
    files = list(pathlib.Path(deploy_dir).iterdir())
    files_to_deploy = list(filter(lambda x: x.suffix in [".yaml", ".yml"], files))
    env.set_variable_files(variables_files)

    organizations, solutions, workspaces = load_resources_from_files(files_to_deploy)
    if not (organization or solution or workspace):
        deploy_objects(organizations, "organization")
        deploy_objects(solutions, "solution")
        deploy_objects(workspaces, "workspace")
    else:
        if organization:
            deploy_objects(organizations, "organization")
        elif solution:
            deploy_objects(solutions, "solution")
        elif workspace:
            deploy_objects(workspaces, "workspace")

    final_state = env.get_state_from_local()
    services = final_state.get("services")
    logger.info(f"Deployment summary: {[i for i in services.get('api')]}")
    _ret = [""]
    _ret.append("")
    _ret.append("Deployments: ")
    _ret.append("")
    _ret.append(f"   * Organization   : {services.get('api').get('organization_id', '')}")
    _ret.append(f"   * Solution       : {services.get('api').get('solution_id', '')}")
    _ret.append(f"   * Workspace      : {services.get('api').get('workspace_id', '')}")
    vars = env.get_variables()
    current_working_directory = os.getcwd()
    logfile_path = os.path.join(current_working_directory, "babylon.log")
    logfile_directory = os.path.dirname(logfile_path)
    _logs = [""]
    _logs.append("Babylon Logs: ")
    _logs.append("")
    if vars.get("path_logs"):
        _logs.append(f"   * The Babylon log and error files are generated at: {vars.get('path_logs')}")
    else:
        _logs.append(f"   * The Babylon log and error files are generated at: {logfile_directory}")
    echo(style("\n".join(_ret), fg="green"))
    echo(style("\n".join(_logs), fg="green"))

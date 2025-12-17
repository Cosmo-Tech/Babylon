from logging import getLogger
from pathlib import Path as pathlib_Path
from typing import Iterable

from click import Path as click_Path
from click import argument, command, option
from yaml import safe_dump, safe_load

from Babylon.commands.macro.deploy_organization import deploy_organization
from Babylon.commands.macro.deploy_solution import deploy_solution
from Babylon.commands.macro.deploy_workspace import deploy_workspace
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def load_resources_from_files(files_to_deploy: list[pathlib_Path]) -> tuple[list, list, list]:
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
@argument("deploy_dir", type=click_Path(dir_okay=True, exists=True))
@option(
    "--var-file",
    "variables_files",
    type=click_Path(file_okay=True, exists=True),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)
@option("--organization", is_flag=True, help="Deploy or update an organization.")
@option("--solution", is_flag=True, help="Deploy or update a solution.")
@option("--workspace", is_flag=True, help="Deploy or update a workspace.")
def apply(
    deploy_dir: click_Path,
    organization: bool,
    solution: bool,
    workspace: bool,
    variables_files: Iterable[pathlib_Path],
):
    """Macro Apply"""
    files = list(pathlib_Path(deploy_dir).iterdir())
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
    logger.info(f"Deployment summary: {[i.id for i in services.get('api')]}")

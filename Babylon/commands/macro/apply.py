from logging import getLogger
from pathlib import Path as PathlibPath

from click import Path as ClickPath
from click import argument, command, echo, option, style
from yaml import safe_dump, safe_load

from Babylon.commands.macro.deploy import resolve_inclusion_exclusion
from Babylon.commands.macro.deploy_organization import deploy_organization
from Babylon.commands.macro.deploy_solution import deploy_solution
from Babylon.commands.macro.deploy_webapp import deploy_webapp
from Babylon.commands.macro.deploy_workspace import deploy_workspace
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def load_resources_from_files(files_to_deploy: list[PathlibPath]) -> tuple[list, list, list]:
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
    webapps = list(filter(lambda x: x.get("kind") == "Webapp", resources))
    return (organizations, solutions, workspaces, webapps)


def deploy_objects(objects: list, object_type: str, deploy_dir: PathlibPath):
    for o in objects:
        content = o.get("content")
        namespace = o.get("namespace")
        if object_type == "organization":
            deploy_organization(namespace=namespace, file_content=content)
        elif object_type == "solution":
            deploy_solution(namespace=namespace, file_content=content)
        elif object_type == "workspace":
            deploy_workspace(namespace=namespace, file_content=content, deploy_dir=deploy_dir)
        elif object_type == "webapp":
            deploy_webapp(namespace=namespace, file_content=content)


def print_section(data: dict, highlight_urls: bool = False):
    for key, value in data.items():
        if not value:
            continue
        label = f"  • {key.replace('_', ' ').title()}"
        styled_label = style(f"{label:<20}:", fg="cyan", bold=True)

        if highlight_urls and "url" in key.lower():
            styled_value = style(str(value).strip(), fg="bright_blue", underline=True)
        else:
            styled_value = style(str(value).strip(), fg="white")

        echo(f"{styled_label} {styled_value}")


@command()
@injectcontext()
@argument("deploy_dir", type=ClickPath(dir_okay=True, exists=True))
@option(
    "--var-file",
    "variables_files",
    type=ClickPath(file_okay=True, exists=True),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)
@option("--include", "include", multiple=True, type=str, help="Specify the resources to deploy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from deployment.")
def apply(
    deploy_dir: ClickPath,
    include: tuple[str],
    exclude: tuple[str],
    variables_files: tuple[PathlibPath],
):
    """Macro Apply"""
    organization, solution, workspace, webapp = resolve_inclusion_exclusion(include, exclude)
    files = list(PathlibPath(deploy_dir).iterdir())
    files_to_deploy = list(filter(lambda x: x.suffix in [".yaml", ".yml"], files))
    env.set_variable_files(variables_files)
    organizations, solutions, workspaces, webapps = load_resources_from_files(files_to_deploy)
    if organization:
        deploy_objects(organizations, "organization", deploy_dir)
    if solution:
        deploy_objects(solutions, "solution", deploy_dir)
    if workspace:
        deploy_objects(workspaces, "workspace", deploy_dir)
    if webapp:
        deploy_objects(webapps, "webapp", deploy_dir)
    final_state = env.get_state_from_local()
    services = final_state.get("services", {})
    api_data = services.get("api", {})
    webapp_data = services.get("webapp", {})
    echo(style("\n📋 Deployment Summary", bold=True, fg="yellow"))
    print_section(api_data)
    print_section(webapp_data)
    echo(style("\n✨ Deployment process complete", fg="white", bold=True))

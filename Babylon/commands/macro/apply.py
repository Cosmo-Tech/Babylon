from logging import getLogger
from pathlib import Path as PathlibPath

from click import Path as ClickPath
from click import argument, command, echo, option, style
from yaml import safe_dump, safe_load

from Babylon.commands.macro.deploy import resolve_inclusion_exclusion
from Babylon.commands.macro.deploy_organization import deploy_organization
from Babylon.commands.macro.deploy_solution import deploy_solution
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
@argument("deploy_dir", type=ClickPath(dir_okay=True, exists=True))
@option("-N", "--namespace", "namespace", required=False, type=str, help="The namespace to apply")
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
    namespace: str | None,
    include: tuple[str],
    exclude: tuple[str],
    variables_files: tuple[PathlibPath],
):
    """Macro Apply"""
    # If a namespace is provided, set it for the environment
    if namespace:
        env.get_ns_from_text(content=namespace)
    organization, solution, workspace = resolve_inclusion_exclusion(include, exclude)
    files = list(PathlibPath(deploy_dir).iterdir())
    files_to_deploy = list(filter(lambda x: x.suffix in [".yaml", ".yml"], files))
    env.set_variable_files(variables_files)
    organizations, solutions, workspaces = load_resources_from_files(files_to_deploy)
    if organization:
        deploy_objects(organizations, "organization")
    if solution:
        deploy_objects(solutions, "solution")
    if workspace:
        deploy_objects(workspaces, "workspace")

    final_state = env.get_state_from_local()
    services = final_state.get("services")
    api_data = services.get("api")
    echo(style("\n📋 Deployment Summary", bold=True, fg="yellow"))
    for key, value in api_data.items():
        if not value:
            continue
        label = f"  • {key.replace('_', ' ').title()}"

        # We pad the label to 20 chars to keep the colons aligned
        styled_label = style(f"{label:<20}:", fg="cyan", bold=True)
        clean_value = str(value).strip()
        styled_value = style(clean_value, fg="white")
        echo(f"{styled_label} {styled_value}")
    echo(style("\n✨ Deployment process complete", fg="white", bold=True))

from logging import getLogger
from pathlib import Path as PathlibPath

from click import Path as ClickPath
from click import argument, command, echo, option, style
from yaml import safe_dump, safe_load

from Babylon.commands.macro.deploy_organization import deploy_organization
from Babylon.commands.macro.deploy_solution import deploy_solution
from Babylon.commands.macro.deploy_webapp import deploy_webapp
from Babylon.commands.macro.deploy_workspace import deploy_workspace
from Babylon.commands.macro.helpers.common import resolve_inclusion_exclusion
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
            resource["file_path"] = f
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

def _find_core_vars(start_dir: PathlibPath) -> PathlibPath | None:
    """Walks up the directory tree to find the core variables file."""
    search = start_dir
    for _ in range(6):
        candidate = search.parent / "core" / "variables.core.yaml"
        if candidate.exists():
            return candidate
        # Stop if we reach the root directory
        if search == search.parent:
            break
        search = search.parent
    return None

def _find_workspace_vars(deploy_dir: PathlibPath) -> list[PathlibPath]:
    """Locates any workspace-specific variable files."""
    # The workspace folder is the parent of deploy_dir (when named "deploy"),
    # or deploy_dir itself otherwise.
    ws_dir = deploy_dir.parent if deploy_dir.name == "deploy" else deploy_dir

    if "workspaces" in ws_dir.parts:
        return sorted(ws_dir.glob("variables*.yaml"))
    return []

def _discover_var_files(deploy_dir: PathlibPath) -> list[PathlibPath]:
    deploy_dir = deploy_dir.resolve()
    found: list[PathlibPath] = []

    # Locate variables.core.yaml
    core_vars = _find_core_vars(deploy_dir)
    if core_vars:
        found.append(core_vars)
        logger.debug(f"  [dim]→ Auto-discovered core vars: {core_vars}[/dim]")
    else:
        logger.warning(
            f"  Could not auto-discover {core_vars} pass --var-file explicitly if needed."
        )

    # Locate workspace variables-N.yaml
    ws_var_files = _find_workspace_vars(deploy_dir)
    for wf in ws_var_files:
        found.append(wf)
        logger.debug(f"  [dim]→ Auto-discovered workspace vars: {wf}[/dim]")

    return found

def print_section(data: dict, highlight_urls: bool = False):
    for key, value in data.items():
        if not value:
            continue
        label = f"  • {key.replace('_', ' ').title()}"
        styled_label = style(f"{label:<20}:", fg="bright_magenta", bold=True)

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
    default=None,
    multiple=True,
    help="Specify the path of your variable file. Defaults to <deploy_dir>/../variables-core.yaml.",
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
    # Auto-discover variable files when none were passed explicitly
    if not variables_files:
        variables_files = tuple(_discover_var_files(PathlibPath(deploy_dir)))
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
    # workspace_id lives in the `workspaces` block; strip any stale flat copy
    # that might still be present in services.api in legacy / not-yet-migrated state.
    api_data = {k: v for k, v in services.get("api", {}).items() if k != "workspace_id"}
    webapp_data = services.get("webapp", {})
    workspaces_data = final_state.get("workspaces", {})

    echo(style("\n📋 Deployment Summary", bold=True, fg="bright_yellow"))

    echo(style("\n ⛁ Shared Resources", fg="bright_cyan", bold=True))
    print_section(api_data)
    print_section(webapp_data, highlight_urls=True)

    if workspaces_data:
        echo(style("\n  ▶ Workspaces", fg="bright_cyan", bold=True))
        for ws_key, ws_state in workspaces_data.items():
            ws_id = ws_state.get("api", {}).get("workspace_id", ws_key)

            # Use a slightly different icon and align it properly
            echo(style(f"    🔸 {ws_id}", fg="bright_magenta", bold=True))

    echo(style("\n✨ Deployment process complete", fg="green", bold=True))

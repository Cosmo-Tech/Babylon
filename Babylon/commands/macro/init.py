from logging import getLogger
from os import getcwd
from pathlib import Path
from shutil import copy

from click import command, echo, option, style

from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


@command()
@option("--project-folder", default="project", help="Name of the project folder to create (default: 'project').")
@option("--variables-file", default="variables.yaml", help="Name of the variables file (default: 'variables.yaml').")
def init(project_folder: str, variables_file: str):
    """
    Scaffolds a new Babylon project structure using YAML templates.
    """
    project_path = Path(getcwd()) / project_folder
    variables_path = Path(getcwd()) / variables_file
    if project_path.exists():
        logger.warning(f"The directory [bold]{project_path}[/bold] already exists")
        return None
    if variables_path.exists():
        logger.warning(f"Configuration file [bold]{variables_file}[/bold] already exists.")
        return None
    project_yaml_files = ["Organization.yaml", "Solution.yaml", "Workspace.yaml", "Dataset.yaml", "Runner.yaml"]
    try:
        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  [dim]→ Created directory: {project_path}[/dim]")
        # Copy Core YAML Templates
        for file in project_yaml_files:
            deploy_file = env.original_template_path / "yaml" / file
            destination = project_path / file
            copy(deploy_file, destination)
            logger.info(f"  [green]✔[/green] Generated [white]{file}[/white]")

        customers_src = env.original_template_path / "yaml" / "dataset" / "customers.csv"
        customers_dst = Path(getcwd()) / "customers.csv"
        copy(customers_src, customers_dst)
        logger.info("  [green]✔[/green] Generated [white]customers.csv[/white]")

        variables_template = env.original_template_path / "yaml" / "variables.yaml"
        copy(variables_template, variables_path)
        logger.info(f"  [green]✔[/green] Generated [white]{variables_file}[/white]")

        # --- 3. Success Summary ---
        echo(style("\n🚀 Project successfully initialized!", fg="green", bold=True))
        echo(style(f"   Path: {project_path}", fg="white", dim=True))
        echo(style("\nNext steps:", fg="white", bold=True))
        echo(style(f"  1. Edit your variables in {variables_file}", fg="cyan"))
        echo(style("  2. Run your first deployment command", fg="cyan"))
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] An error occurred while scaffolding: {e}")

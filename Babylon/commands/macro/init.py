import os
import pathlib
import shutil
from logging import getLogger

from click import command, option

from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@option("--project-folder", default="project", help="Name of the project folder to create (default: 'project').")
@option("--variables-file", default="variables.yaml", help="Name of the variables file (default: 'variables.yaml').")
def init(project_folder: str, variables_file: str):
    """
    Create a Babylon project structure using YAML templates.
    """
    project_path = pathlib.Path(os.getcwd()) / project_folder
    variables_path = pathlib.Path(os.getcwd()) / variables_file
    if project_path.exists():
        logger.info(f"[babylon] The directory '{project_path}' already exists")
        return None
    if variables_path.exists():
        logger.info(f"[babylon] 'variables.yaml' already exists at '{variables_path}'")
        return None
    project_yaml_files = ["Organization.yaml", "Solution.yaml", "Workspace.yaml", "Dataset.yaml", "Runner.yaml"]
    try:
        project_path.mkdir(parents=True, exist_ok=True)
        for file in project_yaml_files:
            deploy_file = pathlib.Path(env.convert_template_path(f"%templates%/yaml/{file}"))
            destination = project_path / file
            shutil.copy(deploy_file, destination)
        variables_template = pathlib.Path(env.convert_template_path("%templates%/yaml/variables.yaml"))
        shutil.copy(variables_template, variables_path)
        logger.info(f"\n[babylon] Project successfully initialized at: {project_path}")
    except Exception as e:
        logger.error(f"[babylon] Error while initializing the project: {e}")

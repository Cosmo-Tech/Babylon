import logging
import pathlib

from click import command
from click import argument
from click import Path
from ruamel.yaml import YAML

from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")

READ_JSON_WORKFLOW = {
    "name": "Import environment variables from a file",
    "id": "import-env",
    "shell": "bash",
    "run": r"""jq -r 'keys[] as $k | "\($k)=\(.[$k])"' config.json >> $GITHUB_ENV"""
}


def update_file(workflow_file: pathlib.Path):
    yaml_loader = YAML()
    with open(workflow_file, "r") as _f:
        data = yaml_loader.load(_f)
    logger.info(f"Updating github workflow {workflow_file}...")
    find = [step for step in data["jobs"]["build_and_deploy_job"]["steps"] if step.get("id") == "import-env"]
    if find:
        logger.warning(f"Workflow {workflow_file} already has the import-env step")
        return
    data["jobs"]["build_and_deploy_job"]["steps"].insert(1, READ_JSON_WORKFLOW)
    with open(workflow_file, "w") as _f:
        yaml_loader.dump(data, _f)
    logger.info(f"Successfully updated workflow file {workflow_file}")


@command()
@argument("workflow_file", type=Path(path_type=Patth(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
def update_workflow(workflow_file: pathlib.Path) -> CommandResponse:
    """Update a github workflow file to read environment from a config.json file during deployment"""
    if not workflow_file.is_dir():
        try:
            update_file(workflow_file)
        except Exception:
            return CommandResponse.fail()
        return CommandResponse.success()
    for file in workflow_file.glob("azure-static-web-apps-*.yml"):
        try:
            update_file(file)
        except Exception:
            return CommandResponse.fail()
    return CommandResponse.success()

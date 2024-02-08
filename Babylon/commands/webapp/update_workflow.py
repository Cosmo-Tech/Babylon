import logging
import pathlib

from click import command
from click import argument
from click import Path
from ruamel.yaml import YAML
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse

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
@wrapcontext()
@argument("workflow_file", type=Path(path_type=pathlib.Path))
def update_workflow(workflow_file: pathlib.Path) -> CommandResponse:
    """
    Update a github workflow file to read environment from a config.json file during deployment
    """
    service = AzureWebAppService()
    service.update_workflow(workflow_file=workflow_file)
    return CommandResponse.success()

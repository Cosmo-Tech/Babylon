import logging
from typing import Optional
import pathlib

from click import command
from click import argument
from click import Path
from click import option
from ruamel.yaml import YAML

from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")

READ_JSON_WORKFLOW = {
    "name": "Import environment variables from a file",
    "id": "import-env",
    "shell": "bash",
    "run": r"""jq -r 'keys[] as $k | "\($k)=\(.[$k])"' config.json >> $GITHUB_ENV"""
}


@command()
@argument("workflow_file", type=Path(path_type=pathlib.Path))
@option("-o",
        "--output_file",
        "output_file",
        help="File to which content should be outputted (json-formatted)",
        type=Path(path_type=pathlib.Path))
def update_workflow(workflow_file: pathlib.Path, output_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """Update a github workflow file to read environment from a config.json file during deployment"""
    output_file = output_file or workflow_file
    yaml_loader = YAML()
    with open(workflow_file, "r") as _f:
        data = yaml_loader.load(_f)
    logger.info(f"Updating github workflow {workflow_file}...")
    find = [step for step in data["jobs"]["build_and_deploy_job"]["steps"] if step.get("id") == "import-env"]
    if find:
        logger.warning(f"Workflow {workflow_file} already has the import-env step")
        return CommandResponse.success()
    data["jobs"]["build_and_deploy_job"]["steps"].insert(1, READ_JSON_WORKFLOW)
    with open(output_file, "w") as _f:
        yaml_loader.dump(data, _f)
    logger.info(f"Successfully saved updated workflow file {output_file}")
    return CommandResponse.success()

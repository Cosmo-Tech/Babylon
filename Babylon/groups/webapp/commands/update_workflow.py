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


@command()
@argument("workflow_file", type=Path(path_type=pathlib.Path))
@option("-c", "--config_file", "config_file", help="Configuration file name", default="config.json")
@option("-o",
        "--output_file",
        "output_file",
        help="File to which content should be outputted (json-formatted)",
        type=Path())
def update_workflow(workflow_file: pathlib.Path,
                    config_file: str,
                    output_file: Optional[str] = None) -> CommandResponse:
    """Update a github workflow file to read environment from a config.json file during deployment"""
    output_file = output_file or workflow_file
    yaml_loader = YAML()
    with open(workflow_file, "r") as _f:
        data = yaml_loader.load(_f)
    logger.info(f"Updating github workflow {workflow_file}...")
    data["jobs"]["build_and_deploy_job"]["steps"] = [{
        "uses": "actions/checkout@v2",
        "with": {
            "submodules": "true"
        }
    }, {
        "name": "Import environment variables from a file",
        "id": "import-env",
        "shell": "bash",
        "run": f"echo \"REACT_APP_BABYLON_CONFIG=$(cat {config_file} | jq '@json')\" >> $GITHUB_ENV"
    }, *data["jobs"]["build_and_deploy_job"]["steps"][1:]]
    with open(output_file, "w") as _f:
        yaml_loader.dump(data, _f)
    logger.info(f"Successfully saved updated workflow file {output_file}")
    return CommandResponse.success()

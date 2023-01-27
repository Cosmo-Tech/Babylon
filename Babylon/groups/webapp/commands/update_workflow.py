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
@option("-o",
        "--output_file",
        "output_file",
        help="File to which content should be outputted (json-formatted)",
        type=Path(),
        required=True)
@option("--env", "env_file", help="Environment file name")
def update_workflow(workflow_file: pathlib.Path, output_file: str, env_file: Optional[str] = None) -> CommandResponse:
    """Update a github workflow file to read env from a file during deployment"""
    env_file = env_file or "deploy.env"
    yaml_loader = YAML()
    with open(workflow_file, "r") as _f:
        data = yaml_loader.load(_f)
    logger.info(f"Updating github workflow {workflow_file}...")
    data["jobs"] = {
        "import_env": {
            "name": "Import environment variables from a file",
            "id": "import-env",
            "shell": "bash",
            "run": f"< {env_file} >> $GITHUB_ENV"
        },
        **data["jobs"]
    }
    with open(output_file, "w") as _f:
        yaml_loader.dump(data, _f)
    logger.info(f"Successfully saved updated workflow file {output_file}")
    return CommandResponse.success()

import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.decorators import working_dir_requires_yaml_key
from ......utils.response import CommandResponse
from ......utils.credentials import pass_tfc_client

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="File to which content should be outputted (json-formatted)",
)
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use")
@option("-m", "--message", "run_message", help="Message added to the run.", default="Run started with Babylon")
@option("--allow_empty_apply", "allow_empty_apply", is_flag=True, help="Can this run have an empty apply ?")
@describe_dry_run("""Would check if WORKSPACE_ID exists

Then create a run for it sending a creation payload""")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@timing_decorator
def run(tfc_client: TFC, workspace_id_wd: str, workspace_id: Optional[str], run_message: str, allow_empty_apply: bool,
        output_file: Optional[pathlib.Path]) -> CommandResponse:
    """Start the run of a workspace

More info on runs can be found at: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run#create-a-run"""
    workspace_id = workspace_id or workspace_id_wd

    try:
        tfc_client.workspaces.show(workspace_id=workspace_id)
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()

    run_payload_template = TEMPLATE_FOLDER_PATH / "terraform_cloud/run_workspace_payload.json"
    with open(run_payload_template) as _f:
        run_payload = json.load(_f)
    run_payload['data']['attributes']['message'] = run_message
    run_payload['data']['attributes']['allow-empty-apply'] = allow_empty_apply
    run_payload['data']['relationships']['workspace']['data']['id'] = workspace_id

    logger.info("Sending payload to API")
    r = tfc_client.runs.create(run_payload)
    logger.info("Run successfully created")
    logger.info(pprint.pformat(r))
    if output_file:
        with open(output_file, "w") as _file:
            json.dump(r['data'], _file, ensure_ascii=False)
    return CommandResponse.success(r.get("data"))

import json
import logging

from click import command
from click import option
from click import argument
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound
from Babylon.utils.decorators import describe_dry_run
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@output_to_file
@pass_tfc_client
@describe_dry_run("Would check if WORKSPACE_ID exists Then create a run for it sending a creation payload")
@option("-m",
        "--message",
        "run_message",
        help="Message added to the run.",
        default="Run started with Babylon",
        type=QueryType())
@option("--allow_empty_apply", "allow_empty_apply", is_flag=True, help="Can this run have an empty apply ?")
@argument("workspace_id", type=QueryType())
def run(tfc_client: TFC, workspace_id: str, run_message: str, allow_empty_apply: bool) -> CommandResponse:
    """
    Start the run of a workspace

    More info on runs can be found at: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run#create-a-run
    """

    try:
        tfc_client.workspaces.show(workspace_id=workspace_id)
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()
    env = Environment()
    run_payload_template = env.working_dir.original_template_path / "tfc/workspace_run.json"
    payload = env.fill_template(run_payload_template, {
        "workspace_id": workspace_id,
        "run_message": run_message,
        "allow_empty_apply": allow_empty_apply
    })
    data = json.loads(payload)

    logger.info("Sending payload to API")
    r = tfc_client.runs.create(data)
    logger.info("Run successfully created")
    return CommandResponse.success(r.get("data"), verbose=True)

import logging

from click import command
from click import argument
from click import option
import git

from ....utils.decorators import require_deployment_key
from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("webapp_repository")
@require_deployment_key("webapp_repository_branch")
@argument("destination_folder")
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the destination folder path be relative to Babylon working directory ?")
def download(webapp_repository: str,
             webapp_repository_branch: str,
             destination_folder: str,
             use_working_dir_file: bool = False) -> CommandResponse:
    """Download the github repository locally"""
    env = Environment()
    if use_working_dir_file:
        destination_folder = env.working_dir.path / destination_folder
    if destination_folder.exists():
        logger.error(f"Local folder {destination_folder} already exists")
        return CommandResponse.fail()
    git.Repo.clone_from(webapp_repository, destination_folder, branch=webapp_repository_branch)
    logger.info(f"Successfully cloned repository {webapp_repository} in folder {destination_folder}")
    return CommandResponse.success()

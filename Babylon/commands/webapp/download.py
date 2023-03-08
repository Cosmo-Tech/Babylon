import logging
import pathlib

from click import command
from click import argument
from click import option
from click import Path
import git

from ...utils.decorators import require_deployment_key
from ...utils.decorators import working_dir_requires_yaml_key
from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("webapp_repository")
@require_deployment_key("webapp_repository_branch")
@working_dir_requires_yaml_key(".secrets.yaml.encrypt", "github.token", "github_token")
@argument("destination_folder", type=Path(path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the destination folder path be relative to Babylon working directory ?")
def download(webapp_repository: str,
             webapp_repository_branch: str,
             github_token: str,
             destination_folder: pathlib.Path,
             use_working_dir_file: bool = False) -> CommandResponse:
    """Download the github repository locally"""
    env = Environment()
    if use_working_dir_file:
        destination_folder = env.working_dir.path / destination_folder
    if destination_folder.exists():
        logger.warning(f"Local folder {destination_folder} already exists, pulling...")
        repo = git.Repo(destination_folder)
        repo.remotes.origin.pull()
        return CommandResponse.success()
    # Will log using the given personal access token
    repo_suffix = webapp_repository.split("github.com/")[1]
    repo_w_token = f"https://oauth2:{github_token}@github.com/{repo_suffix}.git"
    git.Repo.clone_from(repo_w_token, destination_folder, branch=webapp_repository_branch)
    logger.info(f"Successfully cloned repository {webapp_repository} in folder {destination_folder}")
    return CommandResponse.success()

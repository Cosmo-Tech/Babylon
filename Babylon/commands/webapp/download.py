import logging
import pathlib
import git

from typing import Any
from click import command
from click import argument
from click import Path
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@argument("destination_folder", type=Path(path_type=pathlib.Path))
@inject_context_with_resource({'github': ['organization', 'repository', 'branch']})
def download(context: Any, destination_folder: pathlib.Path) -> CommandResponse:
    """
    Download the github repository locally
    """
    repo_org = context['github_organization']
    repo_name = context['github_repository']
    repo_branch = context['github_branch']
    github_secret = env.get_global_secret(resource="github", name="token")
    if destination_folder.exists():
        logger.warning(f"Local folder {destination_folder} already exists, pulling...")
        repo = git.Repo(destination_folder)
        repo.git.checkout(repo_branch)
        repo.remotes.origin.pull()
        return CommandResponse.success()
    # Will log using the given personal access token
    repo_w_token = f"https://oauth2:{github_secret}@github.com/{repo_org}/{repo_name}.git"
    git.Repo.clone_from(repo_w_token, destination_folder, branch=repo_branch)
    logger.info("Successfully cloned")
    return CommandResponse.success()

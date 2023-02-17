import logging
import pathlib

from click import command
from click import argument
from click import option
from click import Path
import git

from ....utils.environment import Environment
from ....utils.response import CommandResponse
from ....utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@command()
@argument("folder", type=Path(path_type=pathlib.Path, file_okay=False, dir_okay=True))
@require_deployment_key("webapp_deployment_repository")
@require_deployment_key("webapp_repository_token")
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the file path be relative to Babylon working directory ?")
def update_remote(folder: pathlib.Path,
                  webapp_deployment_repository: str,
                  webapp_repository_token: str,
                  use_working_dir_file: bool = False) -> CommandResponse:
    """Upload a file to the webapp github repository"""
    env = Environment()
    if use_working_dir_file:
        folder = env.working_dir.path / folder
    repo = git.Repo(folder)
    repo_suffix = webapp_deployment_repository.split("github.com/")[1]
    repo_w_token = f"https://oauth2:{webapp_repository_token}@github.com/{repo_suffix}.git"
    try:
        repo.delete_remote("origin")
    except Exception:
        pass
    remote = repo.create_remote("origin", url=repo_w_token)
    remote.push()
    return CommandResponse.success()

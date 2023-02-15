import logging
import pathlib
import os

from click import command
from click import argument
from click import option
from click import Path
import git

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("file", type=Path(path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the file path be relative to Babylon working directory ?")
def upload_file(file: pathlib.Path, use_working_dir_file: bool = False) -> CommandResponse:
    """Upload a file to the webapp github repository"""
    env = Environment()
    if use_working_dir_file:
        file = env.working_dir.get_file(file)
    # Get parent git repository of the workflow file
    parent_repo = None
    for parent in file.parents:
        if (parent / ".git").exists():
            parent_repo = parent
            break
    repo = git.Repo(parent_repo)
    logger.info(f"Uploading file {file} to remote repository {repo.remotes.origin.url}...")
    # Committing file
    rel_file = os.path.relpath(file, parent_repo)
    repo.index.add(rel_file)
    repo.index.commit(f"Babylon: updated file '{rel_file}'")
    # Pushing commit
    repo.remotes.origin.push()
    logger.info(f"Successfully uploaded file {file} to remote repository {repo.remotes.origin.url}")
    return CommandResponse.success()

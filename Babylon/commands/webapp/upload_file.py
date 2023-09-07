import logging
import pathlib
import os

from click import command
from click import argument
from click import Path
import git

from ...utils.response import CommandResponse
from ...utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("webapp_repository_branch")
@argument("file", type=Path(path_type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path), exists=True))
def upload_file(webapp_repository_branch: str, file: pathlib.Path) -> CommandResponse:
    """Upload a file to the webapp github repository"""
    # Get parent git repository of the workflow file
    parent_repo = None
    for parent in file.parents:
        if (parent / ".git").exists():
            parent_repo = parent
            break
    repo = git.Repo(parent_repo)
    if not repo.active_branch == webapp_repository_branch:
        logger.info(f"Checking out to branch {webapp_repository_branch}")
        repo.git.checkout(webapp_repository_branch)
    # Committing file
    files = [file]
    if file.is_dir():
        files = [f for f in file.glob("*")]
    for file in files:
        logger.info(f"Committing file {file}")
        rel_file = os.path.relpath(file, parent_repo)
        repo.index.add(rel_file)
        repo.index.commit(f"Babylon: updated file '{rel_file}'")
    # Pushing commit
    repo.remotes.origin.push()
    logger.info("Successfully uploaded files to remote repository")
    return CommandResponse.success()

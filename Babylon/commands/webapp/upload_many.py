import logging
import pathlib
import os

from typing import Iterable
from typing import Tuple
from typing import Optional

from click import command, option
from click import argument
from click import Path
import git

from Babylon.utils.typing import QueryType

from ...utils.response import CommandResponse
from ...utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("webapp_repository_branch")
@option("--files",
        "-f",
        "files",
        type=(pathlib.Path),
        multiple=True,
        help="Add a combination <Key Value> that will be sent as parameter to all your datasets")
def upload_many(
        webapp_repository_branch: str,
        files: Optional[Iterable[pathlib.Path]] = None,
    ) -> CommandResponse:
    """Upload many files to the webapp github repository"""
    # Get parent git repository of the workflow file
    parent_repo = None
    for file in files:
        parents = file.parents
        for parent in parents:
            if (parent / ".git").exists():
                parent_repo = parent
                break
        
    repo = git.Repo(parent_repo)
    if not repo.active_branch == webapp_repository_branch:
        logger.info(f"Checking out to branch {webapp_repository_branch}")
        repo.git.checkout(webapp_repository_branch)
    # Getting files
    for file in files:
        rel_file = os.path.relpath(file, parent_repo)
        repo.index.add(rel_file)
        repo.index.commit(f"Babylon: updated file '{rel_file}'")
    # Pushing commit
    repo.remotes.origin.push()
    logger.info("Successfully uploaded files to remote repository")
    return CommandResponse.success()

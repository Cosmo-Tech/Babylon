import os
import logging
import pathlib
import git

from typing import Any
from click import command
from click import argument
from click import Path
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@argument("file", type=Path(path_type=pathlib.Path, exists=True))
@inject_context_with_resource({'github': ['branch', 'repository']})
def upload_file(context: Any, file: pathlib.Path) -> CommandResponse:
    """
    Upload a file to the webapp github repository
    """
    # Get parent git repository of the workflow file
    parent_repo = None
    for parent in file.parents:
        if (parent / ".git").exists():
            parent_repo = parent
            break
    repo = git.Repo(parent_repo)
    if not repo.active_branch == context['github_branch']:
        logger.info(f"Checking out to branch {context['github_branch']}")
        repo.git.checkout(context['github_branch'])
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
    logger.info("Successfully uploaded")
    return CommandResponse.success()

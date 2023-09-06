import os
import git
import logging
import pathlib

from typing import Any, Iterable
from typing import Optional
from click import command, option
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@option("--file",
        "files",
        type=(pathlib.Path),
        multiple=True,
        help="Add a combination <Key Value> that will be sent as parameter to all your datasets")
@inject_context_with_resource({'github': ['branch']})
def upload_many(
    context: Any,
    files: Optional[Iterable[pathlib.Path]] = None,
) -> CommandResponse:
    """
    Upload files to the webapp github repository
    """
    # Get parent git repository of the workflow file
    repo_branch = context['github_branch']
    parent_repo = None
    for file in files:
        parents = file.parents
        for parent in parents:
            if (parent / ".git").exists():
                parent_repo = parent
                break

    repo = git.Repo(parent_repo)
    if not repo.active_branch == repo_branch:
        logger.info(f"Checking out to branch {repo_branch}")
        repo.git.checkout(repo_branch)
    # Getting files
    for file in files:
        rel_file = os.path.relpath(file, parent_repo)
        repo.index.add(rel_file)
        repo.index.commit(f"Babylon: updated file '{rel_file}'")
    # Pushing commit
    repo.remotes.origin.push()
    logger.info("Successfully uploaded")
    return CommandResponse.success()

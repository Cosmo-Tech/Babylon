import os
import git
import json
import logging

from pathlib import Path
from ruamel.yaml import YAML
from typing import Iterable
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()

READ_JSON_WORKFLOW = {
    "name": "Import environment variables from a file",
    "id": "import-env",
    "shell": "bash",
    "run": r"""jq -r 'keys[] as $k | "\($k)=\(.[$k])"' config.json >> $GITHUB_ENV"""
}


def ext_update_file(workflow_file: Path):
    yaml_loader = YAML()
    with open(workflow_file, "r") as _f:
        data = yaml_loader.load(_f)
    logger.info(f"Updating github workflow {workflow_file}...")
    find = [step for step in data["jobs"]["build_and_deploy_job"]["steps"] if step.get("id") == "import-env"]
    if find:
        logger.warning(f"Workflow {workflow_file} already has the import-env step")
        return
    data["jobs"]["build_and_deploy_job"]["steps"].insert(1, READ_JSON_WORKFLOW)
    with open(workflow_file, "w") as _f:
        yaml_loader.dump(data, _f)
    logger.info(f"Successfully updated workflow file {workflow_file}")


class AzureWebAppService:

    def __init__(self, state: dict = None) -> None:
        self.state = state

    def download(self, destination_folder: Path):
        repo_org = self.state["github"]["organization"]
        repo_name = self.state["github"]["repository"]
        repo_branch = self.state["github"]["branch"]
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

    def export_config(self, data: str, config_path: Path):
        config_data = env.fill_template(data=data, state=dict(services=self.state))
        data_json = json.dumps(config_data, indent=2).encode("utf-8")
        config_path.write_bytes(data_json)
        logger.info("Successfully exported")
        return config_data

    def update_workflow(self, workflow_file: Path):
        if not workflow_file.is_dir():
            try:
                ext_update_file(workflow_file)
            except Exception:
                return CommandResponse.fail()
        for file in workflow_file.glob("azure-static-web-apps-*.yml"):
            try:
                ext_update_file(file)
            except Exception:
                return CommandResponse.fail()

    def upload_file(self, file: Path):
        parent_repo = None
        for parent in file.parents:
            if (parent / ".git").exists():
                parent_repo = parent
                break
        repo = git.Repo(parent_repo)
        if not repo.active_branch == self.state["github"]["branch"]:
            logger.info(f'Checking out to branch {self.state["github"]["branch"]}')
            repo.git.checkout(self.state["github"]["branch"])
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

    def upload_many(self, files: Iterable[Path]):
        repo_branch = self.state["github"]["branch"]
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

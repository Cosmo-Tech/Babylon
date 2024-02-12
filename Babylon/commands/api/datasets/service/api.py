import json
import logging
import jmespath

from pathlib import Path
from posixpath import basename
from typing import Optional
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class ApiDatasetService:

    def __init__(self, azure_token: str, state: dict = None) -> None:
        self.state = state
        self.azure_token = azure_token

    def create(self, dataset_file: Path):
        if not dataset_file:
            logger.error("option --payload is missing")
            return None
        if not dataset_file.exists():
            logger.error(f"No such file: '{basename(dataset_file)}' in directory")
            return None
        details = env.fill_template(dataset_file)
        response = oauth_request(
            f'{self.state["api"]["url"]}/organizations/{self.state["api"]["organization_id"]}/datasets',
            self.azure_token,
            type="POST",
            data=details,
        )
        if response is None:
            return None
        dataset = response.json()
        return dataset

    def delete(self, force_validation: bool, id: str):
        if not force_validation and not confirm_deletion("dataset", id):
            return CommandResponse.fail()
        response = oauth_request(
            f'{self.state["api"]["url"]}/organizations/{self.state["api"]["organization_id"]}/datasets/{id}',
            self.azure_token,
            type="DELETE",
        )
        if response is None:
            return None
        return True

    def get_all(self, filter: Optional[str]):
        response = oauth_request(
            f'{self.state["api"]["url"]}/organizations/{self.state["api"]["organization_id"]}/datasets',
            self.azure_token,
        )
        if response is None:
            return None
        datasets = response.json()
        if len(datasets) and filter:
            datasets = jmespath.search(filter, datasets)
        return datasets

    def get(self, id: str):
        org_id = self.state["api"]["organization_id"]
        id = id or self.state["api"]["dataset.id"]
        response = oauth_request(
            f'{self.state["api"]["url"]}/organizations/{org_id}/datasets/{id}',
            self.azure_token,
        )
        if response is None:
            return None
        dataset = response.json()
        return dataset

    def search(self, tag: str):
        details = {"datasetTags": [tag]}
        org_id = self.state["api"]["organization_id"]
        response = oauth_request(
            f'{self.state["api"]["url"]}/organizations/{org_id}/datasets/search',
            self.azure_token,
            type="POST",
            json=details,
        )
        if response is None:
            return None
        dataset = response.json()
        return dataset

    def update(self, dataset_file: Path):
        if not dataset_file.exists():
            logger.error(f"{dataset_file} not found")
            return None
        details = env.fill_template(dataset_file)
        dataset_id = json.loads(details).get("id") or self.state["api"]["dataset.id"]
        response = oauth_request(
            f'{self.state["api"]["url"]}/organizations/{self.state["api"]["organization_id"]}/datasets/{dataset_id}',
            self.azure_token,
            type="PATCH",
            data=details,
        )
        if response is None:
            return None
        dataset = response.json()
        return dataset

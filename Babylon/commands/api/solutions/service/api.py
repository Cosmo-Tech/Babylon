from typing import Optional

from Babylon.utils.request import oauth_request


class SolutionService:
    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token

    def create(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        solution_id = self.state["api"]["solution_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/solutions/{solution_id}", self.azure_token, "POST",
            data=self.spec)
        return response

    def delete(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        solution_id = self.state["api"]["solution_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/solutions/{solution_id}", self.azure_token, "DELETE")
        return response

    def get(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        solution_id = self.state["api"]["solution_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/solutions/{solution_id}", self.azure_token)
        return response

    def get_all(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        solution_id = self.state["api"]["solution_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/solutions", self.azure_token)
        return response

    def update(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        solution_id = self.state["api"]["solution_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/solutions/{solution_id}", self.azure_token, "PATCH")
        return response

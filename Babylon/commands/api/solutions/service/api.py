from typing import Optional

from Babylon.utils.request import oauth_request


class SolutionService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.solution_id = self.state["api"]["solution_id"]

    def create(self):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/solutions",
                                 self.azure_token,
                                 type="POST",
                                 data=self.spec["data"])
        return response

    def delete(self):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
                                 self.azure_token, "DELETE")
        return response

    def get(self):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
                                 self.azure_token)
        return response

    def get_all(self):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/solutions", self.azure_token)
        return response

    def update(self):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
                                 self.azure_token,
                                 "PATCH",
                                 data=self.spec["data"])
        return response

import json
import sys

from logging import getLogger
from typing import Optional
from Babylon.commands.api.workspaces.services.workspaces_security_svc import (
    ApiWorkspaceSecurityService, )
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


class WorkspaceService:

    def __init__(self, state: dict, keycloak_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.keycloak_token = keycloak_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.workspace_id = self.state["api"]["workspace_id"]
        if not self.url:
            logger.error("api url not found verify the state")
            sys.exit(1)
        if not self.organization_id:
            logger.error("Organization id is missing verify the state")
            sys.exit(1)

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces",
            self.keycloak_token,
        )
        return response

    def get(self):
        check_if_workspace_exists(self.workspace_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}",
            self.keycloak_token,
        )
        return response

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces",
            self.keycloak_token,
            type="POST",
            data=details,
        )
        return response

    def update(self):
        check_if_workspace_exists(self.workspace_id)
        details = self.update_payload_with_state()
        details_json = json.dumps(details, indent=4, default=str)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}",
            self.keycloak_token,
            type="PATCH",
            data=details_json,
        )
        return response

    def update_with_payload(self, payload: dict):
        details = payload["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response

    def delete(self, force_validation: bool):
        check_if_workspace_exists(self.workspace_id)
        if not force_validation and not confirm_deletion("workspace", self.workspace_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def update_security(self, old_security: dict):
        security_svc = ApiWorkspaceSecurityService(keycloak_token=self.keycloak_token, state=self.state)
        payload = json.loads(self.spec["payload"])
        security_spec = payload.get("security")
        if not security_spec:
            logger.error("Security is missing")
            sys.exit(1)
        ids_spec = [i.get("id") for i in security_spec["accessControlList"]]
        ids_existing = [i.get("id") for i in old_security["accessControlList"]]
        if "default" in security_spec:
            data = json.dumps(obj={"role": security_spec["default"]}, indent=2, ensure_ascii=True)
            response = security_svc.set_default(data)
            if response is None:
                return CommandResponse.fail()
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    return CommandResponse.fail()
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.add(details)
                if response is None:
                    return CommandResponse.fail()
        for s in ids_existing:
            if s not in ids_spec:
                response = security_svc.delete(id=s)
                if response is None:
                    return CommandResponse.fail()
        return security_spec

    def update_payload_with_state(self):
        jsonPayload = json.loads(self.spec["payload"])
        if self.state["powerbi"].get("workspace.id") and jsonPayload.get('webApp').get(
                "static_domain") and jsonPayload.get('webApp').get('options').get('charts'):
            if self.state["powerbi"]['dashboard_view'] is not None:
                for dashboard_view_tag in self.state["powerbi"]['dashboard_view']:
                    for dashboard in jsonPayload.get('webApp').get('options').get('charts').get('dashboardsView'):
                        if (dashboard_view_tag == dashboard["reportTag"]):
                            dashboard["reportId"] = self.state["powerbi"]['dashboard_view'][dashboard_view_tag]

            if self.state["powerbi"]['scenario_view'] is not None:
                for scenario_view_tag in self.state["powerbi"]['scenario_view']:
                    for scenario in jsonPayload.get('webApp').get('options').get('charts').get('scenarioView'):
                        if isinstance(scenario, dict):
                            if (scenario_view_tag == scenario["reportTag"]):
                                scenario["reportId"] = self.state["powerbi"]['scenario_view'][scenario_view_tag]
                        else:
                            scenarioData = jsonPayload.get('webApp').get('options').get('charts').get(
                                'scenarioView').get(scenario, {})
                            if (scenarioData is not None and scenario_view_tag == scenarioData.get("reportTag")):
                                scenarioData["reportId"] = self.state["powerbi"]['scenario_view'][scenario_view_tag]
        return jsonPayload


def check_if_workspace_exists(dataset_id: str):
    if not dataset_id:
        logger.error("workspace_id is missing check the state or use --workspace-id")
        sys.exit(1)

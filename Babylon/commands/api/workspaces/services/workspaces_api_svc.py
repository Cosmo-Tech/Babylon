import json
import sys

from logging import getLogger
from typing import Optional

from Babylon.commands.api.workspaces.services.workspaces_security_svc import (
    ApiWorkspaceSecurityService, )
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


class WorkspaceService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.azure_token = azure_token
        self.url = state["api"]["url"]
        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        self.organization_id = state["api"]["organization_id"]
        if not self.organization_id:
            logger.error("organization_id not found")
            sys.exit(1)

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces",
            self.azure_token,
        )
        if response is None:
            logger.error('An error occurred while getting of all workspaces')
        return response

    def get(self):
        workspace_id = self.state["api"]["workspace_id"]
        if not workspace_id:
            logger.error("workspace id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
        )
        if response is None:
            logger.error('An error occurred while getting of workspace by workspace_id')
        return response

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces",
            self.azure_token,
            type="POST",
            data=details,
        )
        if response is None:
            logger.error('An error occurred while creating the workspace')
        return response

    def update(self):
        workspace_id = self.state["api"]["workspace_id"]
        details = self.update_payload_with_state()
        details_json = json.dumps(details, indent=4, default=str)
        if not workspace_id:
            logger.error("workspace id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
            type="PATCH",
            data=details_json,
        )
        if response is None:
            logger.error('An error occurred while updating the workspace')
        return response

    def updateWithPayload(self, payload: dict):
        workspace_id = self.state["api"]["workspace_id"]
        details = payload["payload"]
        if not workspace_id:
            logger.error("workspace id not found")
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        if response is None:
            logger.error('An error occurred while updating the workspace')
        return response

    def delete(self, force_validation: bool):
        workspace_id = self.state["api"]["workspace_id"]
        if not workspace_id:
            logger.error("workspace id not found")
            sys.exit(1)
        if not force_validation and not confirm_deletion("workspace", workspace_id):
            return None

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
            type="DELETE",
        )
        if response is None:
            logger.error('An error occurred while workspace deleting')
        return response

    def send_key(self, workspace_id: str, workspace_key: str):
        workspace_id = workspace_id or self.state['api']['workspace_id']
        workspace_key = workspace_key or self.state['api']['workspace_key']
        secret_eventhub = env.get_project_secret(
            organization_id=self.organization_id,
            workspace_key=workspace_key,
            name="eventhub",
        )
        if not secret_eventhub:
            logger.error("[vault] workspace secret key is missing in vault")
            sys.exit(1)
        details = {"dedicatedEventHubKey": secret_eventhub.replace('"', "")}
        details_json = json.dumps(details, indent=4, default=str)
        if not workspace_id:
            logger.error("[api] workspace id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}/secret",
            self.azure_token,
            type="POST",
            data=details_json,
        )
        if response is None:
            logger.error('An error occurred while creating a workspace secret key')
        return response

    def update_security(self, old_security: dict):
        security_svc = ApiWorkspaceSecurityService(azure_token=self.azure_token, state=self.state)
        payload = json.loads(self.spec["payload"])
        security_spec = payload.get("security")
        if not security_spec:
            logger.error("security is missing")
            sys.exit(1)
        ids_spec = [i.get("id") for i in security_spec["accessControlList"]]
        ids_existing = [i.get("id") for i in old_security["accessControlList"]]
        if "default" in security_spec:
            data = json.dumps(obj={"role": security_spec["default"]}, indent=2, ensure_ascii=True)
            response = security_svc.set_default(data)
            if response is None:
                logger.error('An error occurred while updating a default security role in workspace')
                return None
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    logger.error('An error occurred while updating a security role in workspace')
                    return None
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.add(details)
                if response is None:
                    logger.error('An error occurred while adding a security role in workspace')
                    return None
        for s in ids_existing:
            if s not in ids_spec:
                response = security_svc.delete(id=s)
                if response is None:
                    logger.error('An error occurred while deleting a security role in workspace')
        return security_spec

    def update_payload_with_state(self):
        jsonPayload = json.loads(self.spec["payload"])
        if self.state["powerbi"] is not None and jsonPayload.get('webApp') is not None and jsonPayload.get(
                'webApp').get('options').get('charts') is not None:
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

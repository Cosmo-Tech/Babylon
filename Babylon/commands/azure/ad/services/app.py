import logging
import jmespath
import polling2

from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

env = Environment()
logger = logging.getLogger("Babylon")


class AzureDirectoyAppService:

    def __init__(self, azure_token: str, state: dict = None) -> None:
        self.azure_token = azure_token
        self.state = state

    def create(self, details: str):
        logger.info("creating app")
        route = "https://graph.microsoft.com/v1.0/applications"
        handler = polling2.poll(
            lambda: oauth_request(route, self.azure_token, type="POST", data=details),
            check_success=is_correct_response_app,
            step=1,
            timeout=10,
        )
        output_data = handler.json()
        # Service principal creation
        sp_route = "https://graph.microsoft.com/v1.0/servicePrincipals"
        sp_response = polling2.poll(
            lambda: oauth_request(
                sp_route,
                self.azure_token,
                type="POST",
                json={"appId": output_data["appId"]},
            ),
            check_success=is_correct_response_app,
            step=1,
            timeout=10,
        )
        sp_response = sp_response.json()
        if sp_response is None:
            logger.error("[app] Failed to create application service principal")
            return False
        return sp_response, output_data

    def delete(self, object_id: str):
        logger.info(f"[app] deleting app registration {object_id}")
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
        sp_response = polling2.poll(
            lambda: oauth_request(route, self.azure_token, type="DELETE"),
            check_success=is_correct_response_app_deleted,
            step=1,
            timeout=10,
        )
        if sp_response is None:
            logger.info("[app] Successfully deleted")
            return True

    def get_all(self, filter: str = None):
        route = "https://graph.microsoft.com/v1.0/applications"
        response = oauth_request(route, self.azure_token)
        if response is None:
            return CommandResponse.fail()
        response = response.json()
        output_data = response["value"]
        if filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

    def get_principal(self, object_id: str):
        get_route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
        get_response = oauth_request(get_route, self.azure_token)
        if get_response is None:
            return CommandResponse.fail()
        app_id = get_response.json().get("appId")
        route = f"https://graph.microsoft.com/v1.0/servicePrincipals(appId='{app_id}')"
        response = oauth_request(route, self.azure_token)
        if response is None:
            return False
        output_data = response.json()
        return output_data["id"]

    def get(self, object_id: str):
        logger.info(f'[app] getting app {object_id}')
        if not object_id:
            return dict()
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
        response = polling2.poll(
            lambda: oauth_request(route, self.azure_token),
            check_success=is_correct_response_app,
            step=1,
            timeout=10,
        )
        if response is None:
            return False
        output_data = response.json()
        return output_data

    def update(self, object_id: str, details: str):
        logger.info(f'[app] update app {object_id}')
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
        sp_response = oauth_request(route, self.azure_token, type="PATCH", data=details)
        if sp_response is None:
            return False
        logger.info("[app] Successfully updated")
        return True


def is_correct_response_app(response):
    if response is None:
        return False
    output_data = response.json()
    return "id" in output_data


def is_correct_response_app_deleted(response):
    if response is None:
        return None

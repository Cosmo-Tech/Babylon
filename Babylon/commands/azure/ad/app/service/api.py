import logging
import jmespath
import polling2

from click import Path
from Babylon.utils.checkers import check_ascii
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

env = Environment()
logger = logging.getLogger("Babylon")


class AzureDirectoyAppService:

    def __init__(self, azure_token: str) -> None:
        self.azure_token = azure_token

    def create(self, name: str, registration_file: Path = None):
        check_ascii(name)
        route = "https://graph.microsoft.com/v1.0/applications"
        registration_file = (
            registration_file
            or env.working_dir.original_template_path / "webapp/app_registration.yaml"
        )
        details = env.fill_template(registration_file, data={"app_name": name})
        print(details)
        handler = polling2.poll(
            lambda: oauth_request(route, self.azure_token, type="POST", data=details),
            check_success=is_correct_response_app,
            step=1,
            timeout=60,
        )
        output_data = handler.json()
        # Service principal creation
        sp_route = "https://graph.microsoft.com/v1.0/servicePrincipals"
        sp_response = polling2.poll(
            lambda: oauth_request(
                sp_route, self.azure_token, type="POST", json={"appId": output_data["appId"]}
            ),
            check_success=is_correct_response_app,
            step=1,
            timeout=60,
        )
        sp_response = sp_response.json()
        if sp_response is None:
            logger.error("Failed to create application service principal")
            return CommandResponse.fail()
        # env.configuration.set_var(resource_id=r_id, var_name="app_id", var_value=sp_response["appId"])
        # env.configuration.set_var(resource_id=r_id, var_name="name", var_value=sp_response["appDisplayName"])
        # env.configuration.set_var(resource_id=r_id, var_name="principal_id", var_value=sp_response["id"])
        # env.configuration.set_var(resource_id=r_id, var_name="object_id", var_value=output_data["id"])

    def delete(self, object_id: str):
        logger.info(f"Deleting app registration {object_id}")
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
        sp_response = polling2.poll(
            lambda: oauth_request(route, self.azure_token, type="DELETE"),
            check_success=is_correct_response_app_deleted,
            step=1,
            timeout=60,
        )
        if sp_response is None:
            logger.info("Successfully deleted")
            return CommandResponse.success()

    def get_all(self):
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
            return CommandResponse.fail()
        output_data = response.json()
        # env.configuration.set_var(resource_id="app", var_name="principal_id", var_value=output_data["id"])
        return output_data["id"]

    def get(self, object_id: str):
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
        response = polling2.poll(
            lambda: oauth_request(route, self.azure_token),
            check_success=is_correct_response_app,
            step=1,
            timeout=60,
        )
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        # env.configuration.set_var(resource_id=r_id, var_name="app_id", var_value=output_data["appId"])
        # env.configuration.set_var(resource_id=r_id, var_name="name", var_value=output_data["displayName"])
        # env.configuration.set_var(resource_id=r_id, var_name="object_id", var_value=object_id)
        return CommandResponse.success(output_data, verbose=True)

    def update(self, object_id: str, registration_file: str):
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
        details = env.fill_template(registration_file)
        sp_response = polling2.poll(
            lambda: oauth_request(route, self.azure_token, type="PATCH", data=details),
            check_success=is_correct_response_app,
            step=1,
            timeout=60,
        )
        sp_response = sp_response.json()
        if sp_response is None:
            return CommandResponse.fail()
        logger.info("Successfully updated")
        return CommandResponse.success()


def is_correct_response_app(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    return "id" in output_data


def is_correct_response_app_deleted(response):
    if response is None:
        return CommandResponse.fail()

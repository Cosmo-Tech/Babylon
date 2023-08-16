import logging
import pathlib
import polling2

from click import command
from click import option
from click import argument
from click import Path
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token("graph")
@option("--file",
        "registration_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        required=True,
        help="Your custom app description file yaml")
@argument("object_id", type=QueryType())
def update(azure_token: str, object_id: str, registration_file: str) -> CommandResponse:
    """
    Update an app registration in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-update
    """
    route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
    details = env.fill_template(registration_file)
    sp_response = polling2.poll(lambda: oauth_request(route, azure_token, type="PATCH", data=details),
                                check_success=is_correct_response_app,
                                step=1,
                                timeout=60)

    sp_response = sp_response.json()
    if sp_response is None:
        return CommandResponse.fail()
    logger.info("Successfully updated")
    return CommandResponse.success()


def is_correct_response_app(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if "id" in output_data:
        return True

import logging
import pathlib

from typing import Any, Optional
from click import command, argument, option, Path
from Babylon.utils.checkers import check_ascii
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger('Babylon')
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option("--file",
        "file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom appinsight description file yaml")
@argument('name', type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id'], 'webapp': ["location"]})
def create(context: Any, azure_token: str, name: str, file: Optional[pathlib.Path] = None) -> CommandResponse:
    """
    Create a app insight resource in the given resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/create-or-update
    """
    check_ascii(name)
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    create_file = file or env.working_dir.original_template_path / "webapp/app_insight.json"
    details = env.fill_template(create_file)
    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components/{name}?api-version=2015-05-01')

    response = oauth_request(route, azure_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info("Successfully launched")
    return CommandResponse.success(output_data, verbose=True)

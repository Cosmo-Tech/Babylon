import logging
import pathlib
from rich.pretty import pretty_repr
from typing import Optional

from click import command, argument, option, Path

from ....utils.environment import Environment
from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.typing import QueryType

logger = logging.getLogger('Babylon')


@command()
@pass_azure_token()
@require_platform_key('azure_subscription')
@require_platform_key('resource_group_name')
@argument('appinsight_name', type=QueryType())
@option("-f", "--file", "appinsight_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
def create(azure_token: str,
           azure_subscription: str,
           resource_group_name: str,
           appinsight_name: str,
           appinsight_file: Optional[pathlib.Path] = None,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Create a app insight resource in the given resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/create-or-update
    """

    env = Environment()
    create_file = appinsight_file or env.working_dir.payload_path / "webapp/app_insight.json"
    details = env.fill_template(create_file)
    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components/{appinsight_name}?api-version=2015-05-01')

    response = oauth_request(route, azure_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully launched creation of app insight {appinsight_name} "
                f"in resource group {resource_group_name}")
    return CommandResponse.success(output_data)

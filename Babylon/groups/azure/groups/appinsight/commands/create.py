import logging
import pathlib
from rich.pretty import pretty_repr

from azure.core.credentials import AccessToken
from click import command, argument, option, Path
from click import Context, pass_context

from ......utils.environment import Environment
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.decorators import require_platform_key

logger = logging.getLogger('Babylon')


@command()
@pass_context
@require_platform_key('azure_subscription')
@require_platform_key('resource_group_name')
@argument('appinsight_name')
@option("-f", "--file", "create_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path), required=True)
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def create(ctx: Context,
           azure_subscription,
           resource_group_name,
           appinsight_name,
           create_file,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Create a app insight resource in the given resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/create-or-update
    """

    access_token = ctx.find_object(AccessToken).token
    env = Environment()
    if use_working_dir_file:
        create_file = env.working_dir.get_file(str(create_file))
    with open(create_file, "r") as _file:
        data = _file.read()
    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components/{appinsight_name}?api-version=2015-05-01')

    response = oauth_request(route, access_token, type="PUT", data=data)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully launched creation of app insight {appinsight_name}"
                f"in resource group {resource_group_name}")
    return CommandResponse.success(output_data)

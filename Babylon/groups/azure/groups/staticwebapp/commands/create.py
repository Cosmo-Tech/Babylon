import logging
import pathlib

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import argument
from click import Path
from click import option
from rich.pretty import pretty_repr
import git

from ......utils.environment import Environment
from ......utils.request import oauth_request
from ......utils.request import poll_request
from ......utils.decorators import require_platform_key
from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")

DEFAULT_PAYLOAD_TEMPLATE = ".payload_templates/webapp/webapp_details.json"


@command()
@pass_context
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@require_deployment_key("webapp_repository")
@require_deployment_key("webapp_repository_branch")
@require_deployment_key("webapp_repository_token")
@argument("webapp_name")
@option("-f", "--file", "create_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
@option("-w", "--wait", "wait", is_flag=True, help="Should the command return after resource has been created ?")
def create(ctx: Context,
           azure_subscription: str,
           resource_group_name: str,
           webapp_repository: str,
           webapp_repository_branch: str,
           webapp_repository_token: str,
           webapp_name: str,
           create_file: str,
           use_working_dir_file: bool = False,
           wait: bool = False) -> CommandResponse:
    """
    Create a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    access_token = ctx.find_object(AccessToken).token
    env = Environment()
    create_file = create_file or env.working_dir.get_file(DEFAULT_PAYLOAD_TEMPLATE)
    details = env.fill_template(create_file, use_working_dir_file=use_working_dir_file)
    route = (f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
             f"providers/Microsoft.Web/staticSites/{webapp_name}?api-version=2022-03-01")
    response = oauth_request(route, access_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully launched creation of webapp {webapp_name} in resource group {resource_group_name}")
    if not wait:
        return CommandResponse.success(output_data)
    # Waiting for github action to be created
    hostname = output_data["properties"]["defaultHostname"].split(".")[0]

    repo_suffix = webapp_repository.split("github.com/")[1]
    repo_w_token = f"https://oauth2:{webapp_repository_token}@github.com/{repo_suffix}.git"
    print(repo_w_token)
    repo = git.Repo(repo_w_token)
    workflow_file = repo.get_contents(f".github/workflows/azure-static-web-apps-{hostname}.yml")
    print(workflow_file)
    return CommandResponse.success(output_data)

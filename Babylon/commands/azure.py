import json
import subprocess
from pprint import pformat

import cosmotech_api
from azure.identity import AzureCliCredential
from azure.mgmt.subscription import SubscriptionClient
from click.core import Context
from clk.decorators import group
from clk.decorators import option
from clk.decorators import pass_context
from clk.log import get_logger
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.api.workspace_api import WorkspaceApi

from Babylon.utils.azure_identity_credentials_adapter import AzureIdentityCredentialAdapter

LOGGER = get_logger(__name__)


def stripNone(data):
    if isinstance(data, dict):
        return {k: stripNone(v) for k, v in data.items() if k is not None and v is not None}
    elif isinstance(data, list):
        return [stripNone(item) for item in data if item is not None]
    elif isinstance(data, tuple):
        return tuple(stripNone(item) for item in data if item is not None)
    elif isinstance(data, set):
        return {stripNone(item) for item in data if item is not None}
    else:
        return data


def log_response(resp_object, clear_none=True):
    _r = resp_object
    if clear_none:
        _r = stripNone(resp_object)
    LOGGER.debug(pformat(_r))


@group(handle_dry_run=True)
@option('--api_url', type=str, help="The url for the cosmo api")
@option('--api_scope', type=str, help="The scope of the cosmo api")
@option('--organization_id', type=str, help="The id of the organization in the cosmo api")
@option('--workspace_id', type=str, help="The id of the workspace in the cosmo api")
@pass_context
def azure(ctx: Context,
          api_url: str,
          api_scope: str,
          organization_id: str,
          workspace_id: str):
    """Azure subcommand group"""
    LOGGER.debug("deployment parameters :")
    LOGGER.debug(f"          api_url : {api_url}")
    LOGGER.debug(f"        api_scope : {api_scope}")
    LOGGER.debug(f"  organization_id : {organization_id}")
    LOGGER.debug(f"     workspace_id : {workspace_id}")

    LOGGER.debug(f"Finding Azure Credentials")
    credentials = AzureCliCredential()
    if None not in [api_url, api_scope, organization_id, workspace_id]:
        LOGGER.debug(f"Getting access token for given api scope")
        token = credentials.get_token(api_scope)

        LOGGER.debug(f"Generating configuration to access cosmotech api")
        configuration = cosmotech_api.Configuration(
            host=api_url,
            discard_unknown_keys=True,
            access_token=token.token
        )

        ctx.params['api_configuration'] = configuration
    ctx.params['azure_credentials'] = credentials


@azure.command()
@pass_context
def organization(ctx: Context):
    """Test command"""
    if 'api_configuration' not in ctx.parent.params:
        LOGGER.error('Missing api parameters')
        return -1
    LOGGER.debug(f"Opening client to access the cosmotech api")
    with cosmotech_api.ApiClient(ctx.parent.params.get('api_configuration')) as api_client:
        api_orga = OrganizationApi(api_client)
        try:
            LOGGER.debug("Querying the api to get info on the organization")
            r = api_orga.find_organization_by_id(organization_id=ctx.parent.params.get('organization_id'))
            log_response(r)
        except cosmotech_api.exceptions.UnauthorizedException as _e:
            LOGGER.error("Unauthorized access to the cosmotech api")
            return


@azure.command()
@pass_context
def workspace(ctx: Context):
    """Test command"""
    if 'api_configuration' not in ctx.parent.params:
        LOGGER.error('Missing api parameters')
        return -1
    LOGGER.debug(f"Opening client to access the cosmotech api")
    with cosmotech_api.ApiClient(ctx.parent.params.get('api_configuration')) as api_client:
        api_ws = WorkspaceApi(api_client)
        api_sol = SolutionApi(api_client)
        try:
            LOGGER.debug(f"Querying the api to find the current workspace")
            r = api_ws.find_workspace_by_id(organization_id=ctx.parent.params.get('organization_id'),
                                            workspace_id=ctx.parent.params.get('workspace_id')).to_dict()
            LOGGER.debug(f"Workspace query results:")
            log_response(r)
            workspace_key = r['key']
            solution_id = r['solution']['solution_id']
        except cosmotech_api.exceptions.UnauthorizedException as _e:
            LOGGER.error("Unauthorized access to the cosmotech api")
            return
        try:
            LOGGER.debug(f"Querying the api to find the solution linked to the current workspace")
            r = api_sol.find_solution_by_id(organization_id=ctx.parent.params.get('organization_id'),
                                            solution_id=solution_id).to_dict()
            LOGGER.debug(f"Solution query results:")
            log_response(r)
            solution_key = r['key']
        except cosmotech_api.exceptions.UnauthorizedException as _e:
            LOGGER.error("Unauthorized access to the cosmotech api")
            return
        LOGGER.info(f"Workspace  {ctx.parent.params.get('workspace_id')} : {workspace_key}")
        LOGGER.info(f"Solution {solution_id} : {solution_key}")


@azure.command()
@pass_context
def subscriptions(ctx: Context):
    """List available subscriptions"""
    subscription_client = SubscriptionClient(
        credentials=AzureIdentityCredentialAdapter(ctx.parent.params.get('azure_credentials')))
    sub_list = list(subscription_client.subscriptions.list())
    for subscription in sub_list:
        LOGGER.debug(f'{subscription.subscription_id} : {subscription.display_name}')
    else:
        LOGGER.info(f"Total : {len(sub_list)} subscriptions available")


@azure.command()
@option('--subscription', type=str, help='The subscription id from which the applications have to be listed')
@pass_context
def applications(ctx: Context, subscription: str):
    """List available subscriptions"""
    # resource_client = ResourceManagementClient(
    #     credentials=AzureIdentityCredentialAdapter(ctx.parent.params.get('azure_credentials')),
    #     subscription_id=subscription
    # )
    # for r in resource_client.resources.list():
    #     print(r.name, ":", r.type)
    subprocess.check_output(['/bin/sh', '-c', f'az account set --subscription {subscription}'])
    r = json.loads(subprocess.check_output(['/bin/sh', '-c', 'az ad app list --all'], stderr=subprocess.DEVNULL))
    for app in r:
        LOGGER.debug(f"{app['objectId']} : {app['displayName']}, {app['identifierUris']}")
    LOGGER.info(f"Total : {len(r)} app registered")

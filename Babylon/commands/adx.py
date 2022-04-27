import cosmotech_api
from CosmoTech_Acceleration_Library.Accelerators.adx_wrapper import ADXQueriesWrapper
from click.core import Context
from clk.decorators import argument
from clk.decorators import group
from clk.decorators import pass_context
from clk.log import get_logger
from cosmotech_api.api.workspace_api import WorkspaceApi

from Babylon.utils.context import ContextObj

LOGGER = get_logger(__name__)


@group(handle_dry_run=True)
@pass_context
def adx(ctx: Context):
    """
adx subcommand group

This group allows interactions with ADX databases used for a deployment.

The following data are required to use the group :

- cluster_name : the name of a cluster in ADX (ex : phoenixdev)

- cluster_region : the region were the cluster is in Azure (ex : westeurope)
    """
    obj = ContextObj(LOGGER)
    ctx.obj = obj


@adx.command()
@argument("script_path")
@pass_context
def check_db_script(ctx, script_path: str):
    """Test command"""
    if ctx.parent.obj.api_configuration is None:
        LOGGER.error('Missing api parameters')
        return -1
    LOGGER.debug(f"Opening client to access the cosmotech api")
    with cosmotech_api.ApiClient(ctx.parent.obj.api_configuration) as api_client:
        api_ws = WorkspaceApi(api_client)
        try:
            LOGGER.debug(f"Querying the api to find the current workspace key")
            r = api_ws.find_workspace_by_id(organization_id=ctx.parent.obj.config.get('organization_id'),
                                            workspace_id=ctx.parent.obj.config.get('workspace_id')).to_dict()
            workspace_key = r['key']
        except cosmotech_api.exceptions.UnauthorizedException as _e:
            LOGGER.error("Unauthorized access to the cosmotech api")
            return
    database_name = ctx.parent.obj.config.get('organization_id') + "-" + workspace_key
    LOGGER.debug(f"Database name : {database_name}")
    wrapper = ADXQueriesWrapper(database=database_name, cluster_name=ctx.parent.obj.config.get('cluster_name'),
                                cluster_region=ctx.parent.obj.config.get('cluster_region'))
    r = wrapper.run_command_query(".show tables details|project TableName")
    for t in r.tables[0]:
        print(t)
    pass

from CosmoTech_Acceleration_Library.Accelerators.adx_wrapper import ADXQueriesWrapper
from click.core import Context
from click import argument
from click import group
from click import pass_context
from logging import getLogger

from azure.mgmt.kusto import KustoManagementClient
from azure.core.exceptions import HttpResponseError

from .utils.context import ContextObj

from pprint import pformat
import time

LOGGER = getLogger("Babylon")


@group()
@pass_context
def adx(ctx: Context):
    """
adx subcommand group
    """
    obj = ContextObj(LOGGER, azure=True, api=False, config=True)
    ctx.obj = obj


@adx.command()
@argument("script_path")
@pass_context
def run_db_script(ctx: Context, script_path: str):
    """Allow the run of a kql script on the target database.

Requires the user to have admin rights on the given database.

The function will list the tables available on the base after the script ran."""
    if not ctx.parent.obj.check_required_configuration(
        ['azure_subscription', 'resource_group_name', 'cluster_name', 'cluster_region', 'database_name']):
        return
    db_desc = f"{ctx.parent.obj.config.get('cluster_name')}" \
              f".{ctx.parent.obj.config.get('cluster_region')}/" \
              f"{ctx.parent.obj.config['database_name']}"
    kmc = KustoManagementClient(credential=ctx.parent.obj.azure_credentials,
                                subscription_id=ctx.parent.obj.config['azure_subscription'])

    script_name = f"BabylonScript{(time.time() // 1)}"
    with open(script_path) as script_file:
        script_content = script_file.read()
        LOGGER.debug(f"Running the following script on {db_desc}:")
        LOGGER.debug(script_content)
        start_time = time.time()
        s = kmc.scripts.begin_create_or_update(resource_group_name=ctx.parent.obj.config['resource_group_name'],
                                               cluster_name=ctx.parent.obj.config['cluster_name'],
                                               database_name=ctx.parent.obj.config['database_name'],
                                               script_name=script_name,
                                               parameters={"script_content": script_content})
        try:
            while not s.done():
                s.wait(1)
        except HttpResponseError as _resp_error:
            LOGGER.error("Script run failed :")
            LOGGER.error(_resp_error.message)
        else:
            LOGGER.info(f"Script ran on {db_desc}")
        LOGGER.debug(f"Script used {time.time() - start_time}s to run.")


@adx.command()
@pass_context
def list_tables(ctx: Context):
    """List all tables in the ADX database"""
    if not ctx.parent.obj.check_required_configuration(
        ['azure_subscription', 'resource_group_name', 'cluster_name', 'cluster_region', 'database_name']):
        return
    db_desc = f"{ctx.parent.obj.config.get('cluster_name')}" \
              f".{ctx.parent.obj.config.get('cluster_region')}/" \
              f"{ctx.parent.obj.config['database_name']}"
    wrapper = ADXQueriesWrapper(database=ctx.parent.obj.config['database_name'],
                                cluster_name=ctx.parent.obj.config.get('cluster_name'),
                                cluster_region=ctx.parent.obj.config.get('cluster_region'))
    LOGGER.debug(f"Connection string : {wrapper.cluster_kcsb}")
    r = wrapper.run_command_query(".show tables details|project TableName")
    LOGGER.info(f"List of the tables on {db_desc} post to script:")
    for t in sorted(list(map(lambda l: l[0], list(r.tables[0])))):
        LOGGER.info(f"  - {t}")


@adx.command()
@pass_context
def test_mgmt(ctx: Context):
    """Display accessible info on the ADX connection using the management API"""
    if not ctx.parent.obj.check_required_configuration(
        ['azure_subscription', 'resource_group_name', 'cluster_name', 'cluster_region', 'database_name']):
        return
    kmc = KustoManagementClient(credential=ctx.parent.obj.azure_credentials,
                                subscription_id=ctx.parent.obj.config['azure_subscription'])

    cluster = kmc.clusters.get(cluster_name=ctx.parent.obj.config['cluster_name'],
                               resource_group_name=ctx.parent.obj.config['resource_group_name'])
    LOGGER.info(pformat(cluster.serialize(keep_readonly=True)))
    database = kmc.databases.get(resource_group_name=ctx.parent.obj.config['resource_group_name'],
                                 cluster_name=ctx.parent.obj.config['cluster_name'],
                                 database_name=ctx.parent.obj.config['database_name'])
    LOGGER.info(pformat(database.serialize(keep_readonly=True)))
    scripts = kmc.scripts.list_by_database(resource_group_name=ctx.parent.obj.config['resource_group_name'],
                                           cluster_name=ctx.parent.obj.config['cluster_name'],
                                           database_name=ctx.parent.obj.config['database_name'])
    for script in scripts:
        LOGGER.info(pformat(script.serialize(keep_readonly=True)))

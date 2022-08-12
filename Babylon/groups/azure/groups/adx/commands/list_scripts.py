import logging

import click
from azure.mgmt.kusto import KustoManagementClient
from click import make_pass_decorator

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ......utils.decorators import timing_decorator

pass_kmc = make_pass_decorator(KustoManagementClient)

logger = logging.getLogger("Babylon")


@click.command()
@pass_kmc
@require_platform_key("cluster_name", "cluster_name")
@require_platform_key("resource_group_name", "resource_group_name")
@require_deployment_key("database_name", "database_name")
@timing_decorator
def list_scripts(kmc: KustoManagementClient, cluster_name: str, resource_group_name: str, database_name: str):
    """List scripts on the database"""
    r = kmc.scripts.list_by_database(resource_group_name=resource_group_name,
                                     cluster_name=cluster_name,
                                     database_name=database_name)
    for script in r:
        logger.info(f"{script.name}")

from click import group

from Babylon.utils.environment import Environment

from .client import *

@group()
def api():
    """Cosmotech API"""
    pass


for _command in [
    about,
    query_data,
    create_organization,
    delete_organization,
    list_organizations,
    create_solution,
    create_workspace,
    create_runner,
    create_dataset,
    create_dataset_part,
    list_workspaces,
    list_datasets,
    list_runners,
    list_solutions,
    list_dataset_parts,
    delete_solution,
    delete_workspace,
    delete_runner,
    delete_dataset,
    delete_dataset_part,
    get_organization,
    get_solution,
    get_workspace,
    get_dataset,
    get_runner,
    get_dataset_part,
    update_organization,
    update_solution,
    update_workspace,
    update_runner,
    update_dataset,
    update_dataset_part,
    start_run,
    stop_run,
    get_run,
    delete_run,
    get_run_logs,
    get_run_status,
    list_runs,
]:
    api.add_command(_command)

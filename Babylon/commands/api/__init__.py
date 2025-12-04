from click import group

from Babylon.utils.environment import Environment

from .client import (
    create_dataset,
    create_organization,
    create_runner,
    create_solution,
    create_workspace,
    delete_dataset,
    delete_organization,
    delete_runner,
    delete_solution,
    delete_workspace,
    get_dataset,
    get_organization,
    get_runner,
    get_solution,
    get_workspace,
    list_datasets,
    list_organizations,
    list_runners,
    list_solutions,
    list_workspaces,
    update_dataset,
    update_organization,
    update_runner,
    update_solution,
    update_workspace,
)
from .datasets import datasets
from .meta.about import about
from .organizations import organizations
from .runners import runners
from .runs import runs
from .solutions import solutions
from .workspaces import workspaces

env = Environment()


@group()
def api():
    """Cosmotech API"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


list_groups = [workspaces, datasets, organizations, solutions, runners, runs]

for _group in list_groups:
    api.add_command(_group)

api.add_command(about)
for _command in [
    create_organization,
    delete_organization,
    list_organizations,
    create_solution,
    create_workspace,
    create_runner,
    create_dataset,
    list_workspaces,
    list_datasets,
    list_runners,
    list_solutions,
    delete_solution,
    delete_workspace,
    delete_runner,
    delete_dataset,
    get_organization,
    get_solution,
    get_workspace,
    get_dataset,
    get_runner,
    update_organization,
    update_solution,
    update_workspace,
    update_runner,
    update_dataset,
]:
    api.add_command(_command)

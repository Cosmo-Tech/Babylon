from click import group
from Babylon.utils.environment import Environment
from .datasets import datasets
from .organizations import organizations
from .runs import runs
from .solutions import solutions
from .workspaces import workspaces
from .runners import runners

env = Environment()


@group()
def api():
    """Cosmotech API"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


list_groups = [workspaces, datasets, organizations, solutions, runners, runs]

for _group in list_groups:
    api.add_command(_group)

from click import group
from Babylon.utils.environment import Environment
from .connectors import connectors
from .datasets import datasets
from .organizations import organizations
from .scenarioruns import scenarioruns
from .solutions import solutions
from .workspaces import workspaces
from .scenarios import scenarios

env = Environment()


@group()
def api():
    """Cosmotech API"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


list_groups = [workspaces, datasets, connectors, organizations, solutions, scenarios, scenarioruns]

for _group in list_groups:
    api.add_command(_group)

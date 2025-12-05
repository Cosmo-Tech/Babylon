from click import group

from Babylon.utils.environment import Environment

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
    pass


list_groups = [workspaces, datasets, organizations, solutions, runners, runs]

for _group in list_groups:
    api.add_command(_group)

api.add_command(about)

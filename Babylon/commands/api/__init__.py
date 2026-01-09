from click import group

from .dataset import datasets
from .meta import about
from .organization import organizations
from .run import runs
from .runner import runners
from .solution import solutions
from .workspace import workspaces


@group()
def api():
    """Cosmotech API"""
    pass


for _command in [organizations, solutions, workspaces, datasets, runners, runs, about]:
    api.add_command(_command)

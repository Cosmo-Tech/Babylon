from click import group

from .connector import connector
from .dataset import dataset
from .organization import organization
from .solution import solution
from .workspace import workspace


@group()
def api():
    """Group handling communication with the cosmotech API"""
    pass


list_groups = [
    workspace,
    dataset,
    connector,
    organization,
    solution
]

for _group in list_groups:
    api.add_command(_group)

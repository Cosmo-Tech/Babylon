from .connector import connector
from .dataset import dataset
from .organization import organization
from .solution import solution
from .workspace import workspace

list_groups = [
    workspace,
    dataset,
    connector,
    organization,
    solution,
]

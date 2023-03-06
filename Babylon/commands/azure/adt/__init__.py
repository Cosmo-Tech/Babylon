from click import group

from .instance import instance
from .model import model

list_groups = [
    model,
    instance,
]


@group()
def adt():
    """Allow communication with Azure Digital Twin"""


for _group in list_groups:
    adt.add_command(_group)

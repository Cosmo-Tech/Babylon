from click import group
from .container import container
from .policy import policy

list_groups = [container, policy]


@group()
def storage():
    """Azure Storage Blob"""
    pass


for _group in list_groups:
    storage.add_command(_group)

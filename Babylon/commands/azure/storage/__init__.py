from click import group
from .container import container

list_groups = [
    container,
]


@group()
def storage():
    """Azure Storage Blob"""
    pass


for _group in list_groups:
    storage.add_command(_group)

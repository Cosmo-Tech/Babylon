from click import group

from .upload import upload

list_commands = [upload]


@group()
def container():
    """Azure Storage Blob containers"""
    pass


for _command in list_commands:
    container.add_command(_command)

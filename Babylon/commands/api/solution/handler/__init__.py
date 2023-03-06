from click import group

from .download import download
from .upload import upload


@group()
def handler():
    """Group allowing solution handler management"""
    pass


list_commands = [
    download,
    upload,
]

for _command in list_commands:
    handler.add_command(_command)

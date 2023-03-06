from click import group

from .list import list
from .upload import upload

list_commands = [
    upload,
    list,
]


@group()
def model():
    """Subgroup dedicate to Azure digital twins models management"""
    pass


for _command in list_commands:
    model.add_command(_command)

from click import group

from .get_all import get_all
from .upload import upload

list_commands = [
    upload,
    get_all,
]


@group()
def model():
    """Subgroup dedicate to Azure digital twins models management"""
    pass


for _command in list_commands:
    model.add_command(_command)

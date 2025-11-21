from click import group

from .get import get
from .store import store

list_commands = [
    store,
    get,
]


@group()
def token():
    """Azure access token"""
    pass


for _command in list_commands:
    token.add_command(_command)

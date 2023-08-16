from click import group
from .store import store
from .get import get

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

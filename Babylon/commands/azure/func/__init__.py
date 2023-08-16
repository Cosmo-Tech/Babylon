from click import group
from .deploy import deploy

list_commands = [
    deploy,
]


@group()
def func():
    """Azure scenario download function"""
    pass


for _command in list_commands:
    func.add_command(_command)

from click import group
from .deploy import deploy
from .delete import delete

list_commands = [deploy, delete]


@group()
def func():
    """Azure scenario download function"""
    pass


for _command in list_commands:
    func.add_command(_command)

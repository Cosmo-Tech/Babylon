from click import group

from .add import add

list_commands = [add]


@group()
def users():
    """Command group handling PowerBI dataset users"""
    pass


for _command in list_commands:
    users.add_command(_command)

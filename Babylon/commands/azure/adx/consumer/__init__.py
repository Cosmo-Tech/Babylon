from click import group
from .add import add

list_commands = [
    add,
]


@group()
def consumer():
    """Consumers Event Hub"""
    pass


for _command in list_commands:
    consumer.add_command(_command)

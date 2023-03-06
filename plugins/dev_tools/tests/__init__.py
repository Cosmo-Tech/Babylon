from click import group

from .how_to import how_to

list_commands = [
    how_to
]


@group()
def tests():
    """Sub group for test commands"""
    pass


for _command in list_commands:
    tests.add_command(_command)

from click import group
from .set import set

list_commands = [set]


@group(name="iam")
def permission():
    """Azure Access Control IAM"""
    pass


for _command in list_commands:
    permission.add_command(_command)

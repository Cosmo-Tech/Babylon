from click import group

from .script import script
from .permission import permission
from .get_all import get_all
from .database import database
from .connections import connections_group

list_commands = [get_all]

list_groups = [permission, script, database, connections_group]


@group()
def adx():
    """Group interacting with Azure Data Explorer"""
    pass


for _command in list_commands:
    adx.add_command(_command)

for _group in list_groups:
    adx.add_command(_group)

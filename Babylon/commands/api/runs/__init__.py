from click import group

from Babylon.commands.api.runs.delete import delete
from Babylon.commands.api.runs.get import get
from Babylon.commands.api.runs.get_all import get_all
from Babylon.commands.api.runs.logs import logs
from Babylon.commands.api.runs.status import status


@group()
def runs():
    """Runs - Cosmotech API"""
    pass


list_commands = [logs, status, get, get_all, delete]

for _command in list_commands:
    runs.add_command(_command)

from click import group

from Babylon.commands.api.runs.cumulated_logs import cumulated_logs
from Babylon.commands.api.runs.logs import logs
from Babylon.commands.api.runs.status import status
from Babylon.commands.api.runs.stop import stop


@group()
def runs():
    """Runs - Cosmotech API"""
    pass


list_commands = [cumulated_logs, logs, status, stop]

for _command in list_commands:
    runs.add_command(_command)

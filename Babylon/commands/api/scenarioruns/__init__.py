from click import group

from Babylon.commands.api.scenarioruns.cumulated_logs import cumulated_logs
from Babylon.commands.api.scenarioruns.logs import logs
from Babylon.commands.api.scenarioruns.status import status
from Babylon.commands.api.scenarioruns.stop import stop


@group()
def scenarioruns():
    """Scenarioruns - Cosmotech API"""
    pass


list_commands = [cumulated_logs, logs, status, stop]

for _command in list_commands:
    scenarioruns.add_command(_command)

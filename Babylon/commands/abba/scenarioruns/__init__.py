from click import group

from Babylon.commands.abba.scenarioruns.cumulatedlogs import cumulatedlogs
from Babylon.commands.abba.scenarioruns.logs import logs
from Babylon.commands.abba.scenarioruns.status import status
from Babylon.commands.abba.scenarioruns.stop import stop


@group()
def scenarioruns():
    """Scenarioruns - Cosmotech ABBA"""
    pass


list_commands = [cumulatedlogs, logs, status, stop]

for _command in list_commands:
    scenarioruns.add_command(_command)

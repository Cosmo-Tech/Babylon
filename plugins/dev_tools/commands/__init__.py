from .parameter_value import parameter_value
from .initialize_command import initialize_command
from .initialize_group import initialize_group
from .initialize_plugin import initialize_plugin
from .list_required_keys import list_required_keys
from .move_group import move_group
from .rename_command import rename_command

list_commands = [
    parameter_value,
    initialize_plugin,
    list_required_keys,
    move_group,
    rename_command,
    initialize_command,
    initialize_group,
]

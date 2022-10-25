from .get_tests_of_command import get_tests_of_command
from .update_test_command_folder import update_test_command_folder
from .tests_todo import tests_todo
from .initialize_plugin import initialize_plugin
from .list_required_keys import list_required_keys
from .move_group import move_group
from .rename_command import rename_command
from .initialize_command import initialize_command
from .initialize_group import initialize_group

list_commands = [
    get_tests_of_command,
    update_test_command_folder,
    tests_todo,
    initialize_plugin,
    list_required_keys,
    move_group,
    rename_command,
    initialize_command,
    initialize_group,
]

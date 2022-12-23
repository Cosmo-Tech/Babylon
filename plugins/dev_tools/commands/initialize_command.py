import logging
import pathlib
import shutil

from click import argument
from click import command
from click import pass_context
from click import make_pass_decorator

from .initialize_group import initialize_group
from Babylon.utils import TEMPLATE_FOLDER_PATH
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.string import is_valid_command_name

logger = logging.getLogger("Babylon")
pass_base_path = make_pass_decorator(pathlib.Path)


@command()
@argument("group_name", nargs=-1)
@argument("command_name", nargs=1)
@pass_base_path
@pass_context
@timing_decorator
def initialize_command(ctx, base_path: pathlib.Path, group_name: list[str], command_name: str):
    """Will initialize code for COMMAND_NAME and make it available in GROUP_NAME

COMMAND_NAME and GROUP_NAME must only contain alphanumeric characters or -"""
    command_name = command_name.replace("-", "_")
    if not is_valid_command_name(command_name):
        logger.error(f"`{command_name}` contains illegal characters")
        return

    group_name = [name.lower().replace("-", "_") for name in group_name]
    command_name = command_name.lower()

    logger.debug(f"Initializing command `{command_name}` in group `{' '.join(group_name)}`")
    babylon_groups_path = base_path / "groups"
    _g_path = "/groups/".join(group_name)

    if group_name:
        group_path = babylon_groups_path / _g_path
    else:
        group_path = base_path
    command_file_path = group_path / f"commands/{command_name}.py"

    if command_file_path.exists():
        logger.error(f"Command `{' '.join(group_name + [command_name])}` already exists")
        return

    if not group_path.exists():
        logger.info(f"Group `{' '.join(group_name)}` does not exists, creating it")
        ctx.invoke(initialize_group, group_name=group_name)

    template_path = TEMPLATE_FOLDER_PATH / "command_template.py"
    shutil.copy(template_path, command_file_path)

    parent_commands_init = group_path / "commands/__init__.py"
    _pci_content = []
    with open(parent_commands_init) as _pgi_file:
        for _line in _pgi_file:
            _pci_content.append(_line)
    _pci_content.insert(0, f'from .{command_name} import {command_name}\n')
    _pci_content.insert(_pci_content.index('list_commands = [\n') + 1, f'    {command_name},\n')
    with open(parent_commands_init, "w") as _pgi_file:
        _pgi_file.write("".join(_pci_content))

    _cf_content = []
    with open(command_file_path) as _gi_file:
        for _line in _gi_file:
            _cf_content.append(_line.replace('command_template', command_name))
    with open(command_file_path, "w") as _gi_file:
        _gi_file.write("".join(_cf_content))

    logger.info(f"Command `{' '.join(group_name)} {command_name}` was created")
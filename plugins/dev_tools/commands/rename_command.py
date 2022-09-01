import logging
import os
import pathlib

from click import argument
from click import command
from click import make_pass_decorator

from Babylon.utils.decorators import allow_dry_run
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.string import is_valid_command_name
from Babylon.utils.string import to_header_line

logger = logging.getLogger("Babylon")
pass_base_path = make_pass_decorator(pathlib.Path)


@command()
@argument("group_name", nargs=-1)
@argument("old_command_name", nargs=1)
@argument("new_command_name", nargs=1)
@pass_base_path
@allow_dry_run
@timing_decorator
def rename_command(base_path, group_name: list[str], old_command_name: str, new_command_name: str,
                   dry_run: bool = False):
    """Will rename OLD_COMMAND_NAME to NEW_COMMAND_NAME in GROUP_NAME

COMMAND_NAME and GROUP_NAME must only contain alphanumeric characters or -"""
    if not is_valid_command_name(old_command_name.replace("-", "_")):
        logger.error(f"`{old_command_name}` contains illegal characters")
        return
    if not is_valid_command_name(new_command_name.replace("-", "_")):
        logger.error(f"`{new_command_name}` contains illegal characters")
        return
    group_name = [name.lower().replace("-", "_") for name in group_name]
    old_command_name = old_command_name.lower().replace("-", "_")
    new_command_name = new_command_name.lower().replace("-", "_")
    babylon_groups_path = base_path / "groups"
    _g_path = "/groups/".join(group_name)
    if group_name:
        group_path = babylon_groups_path / _g_path
    else:
        group_path = base_path
    old_command_file_path = group_path / f"commands/{old_command_name}.py"
    new_command_file_path = group_path / f"commands/{new_command_name}.py"

    if not old_command_file_path.exists():
        logger.error(f"Command `{' '.join(group_name + [old_command_name.replace('_', '-')])}` does not exists")
        return

    if new_command_file_path.exists():
        logger.error(f"Command `{' '.join(group_name + [new_command_name.replace('_', '-')])}` already exists")
        return

    logger.debug(f"Renaming command `{old_command_name}` in group `{' '.join(group_name)}` to `{new_command_name}`")

    parent_commands_init = group_path / "commands/__init__.py"
    _pci_content = []
    with open(parent_commands_init) as _pgi_file:
        for _line in _pgi_file:
            _pci_content.append(_line.replace(old_command_name, new_command_name))
    if dry_run:
        logger.info(to_header_line(f"Writing {parent_commands_init}"))
        logger.info("".join(_pci_content))
    else:
        with open(parent_commands_init, "w") as _pgi_file:
            _pgi_file.write("".join(_pci_content))

    _cf_content = []
    with open(old_command_file_path) as _gi_file:
        for _line in _gi_file:
            if _line.startswith(f"def {old_command_name}"):
                _cf_content.append(_line.replace(f"def {old_command_name}", f"def {new_command_name}"))
            else:
                _cf_content.append(_line)

    if dry_run:
        logger.info(to_header_line(f"Writing {new_command_file_path}"))
        logger.info("".join(_cf_content))
        logger.info(to_header_line(""))
    else:
        with open(new_command_file_path, "w") as _gi_file:
            _gi_file.write("".join(_cf_content))

    if dry_run:
        logger.info(f"Removing {old_command_file_path}")
    else:
        os.remove(old_command_file_path)

    logger.info(f"Command `{' '.join(group_name + [old_command_name])}` "
                f"was renamed to `{' '.join(group_name + [new_command_name])}`")

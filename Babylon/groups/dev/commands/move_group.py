import glob
import logging
import os
import pathlib
import shutil

from click import command
from click import pass_context
from click.core import Context

from .initialize_group import initialize_group
from ....utils import BABYLON_PATH
from ....utils.decorators import allow_dry_run
from ....utils.decorators import timing_decorator
from ....utils.interactive import ask_for_group
from ....utils.string import is_valid_command_name
from ....utils.string import to_header_line

logger = logging.getLogger("Babylon")


@command()
@pass_context
@allow_dry_run
@timing_decorator
def move_group(ctx: Context, dry_run: bool = False):
    """Command made to move groups"""
    babylon_groups_path = BABYLON_PATH / "groups"

    old_group_name = ask_for_group("Enter an existing group name", True)
    if any([not is_valid_command_name(n.replace("-", "_")) for n in old_group_name]):
        logger.error(f"`{' '.join(old_group_name)}` contains illegal characters (only accept alphanumeric or -)")
        return
    old_group_name = [name.lower().replace("-", "_") for name in old_group_name]

    _old_g_path = "/groups/".join(old_group_name)
    old_group_path = babylon_groups_path / _old_g_path
    if not old_group_path.exists():
        logger.error(f"Group `{' '.join(old_group_name)}` does not exists")
        return

    new_group_name = ask_for_group("Enter the new group name", False)
    if any([not is_valid_command_name(n.replace("-", "_")) for n in new_group_name]):
        logger.error(f"`{' '.join(new_group_name)}` contains illegal characters (only accept alphanumeric or -)")
        return

    new_group_name = [name.lower().replace("-", "_") for name in new_group_name]
    _new_g_path = "/groups/".join(new_group_name)
    new_group_path = babylon_groups_path / _new_g_path
    if new_group_path.exists():
        logger.error(f"Group `{' '.join(new_group_name)}` already exists")
        return

    if len(old_group_name) > 1:
        old_parent_group_path = babylon_groups_path / "/groups/".join(old_group_name[:-1])
    else:
        old_parent_group_path = BABYLON_PATH

    old_parent_group_init = old_parent_group_path / "groups/__init__.py"
    _pgi_content = []
    with open(old_parent_group_init) as _pgi_file:
        for _line in _pgi_file:
            if old_group_name[-1] not in _line:
                _pgi_content.append(_line)
    if dry_run:
        logger.info(to_header_line(f"Updating {old_parent_group_init} to remove new group"))
        logger.info("".join(_pgi_content))
    else:
        logger.info(f"Updating {old_parent_group_init} to remove old group")
        with open(old_parent_group_init, "w") as _pgi_file:
            _pgi_file.write("".join(_pgi_content))

    if len(new_group_name) > 1:
        parent_group_path = babylon_groups_path / "/groups/".join(new_group_name[:-1])
        if not parent_group_path.exists():
            logger.info(
                f"Group `{' '.join(new_group_name[:-1])}` does not exists creating it before creating `{new_group_name[-1]}`.")
            if not dry_run:
                ctx.invoke(initialize_group, group_name=new_group_name[:-1])
    else:
        parent_group_path = BABYLON_PATH

    if dry_run:
        logger.info(to_header_line(f"Moving group to new location"))
        logger.info(f"From: {old_group_path}")
        logger.info(f"To: {new_group_path}")
    else:
        logger.info("Moving group to new location")
        shutil.move(old_group_path, new_group_path)

    parent_group_init = parent_group_path / "groups/__init__.py"
    _pgi_content = []
    with open(parent_group_init) as _pgi_file:
        for _line in _pgi_file:
            _pgi_content.append(_line)
        _pgi_content.insert(0, f'from .{new_group_name[-1]} import {new_group_name[-1]}\n')
        _pgi_content.insert(_pgi_content.index('list_groups = [\n') + 1, f'    {new_group_name[-1]},\n')
    if dry_run:
        logger.info(to_header_line(f"Updating {parent_group_init} to add new group"))
        logger.info("".join(_pgi_content))
    else:
        logger.info(f"Updating {parent_group_init} to add new group")
        with open(parent_group_init, "w") as _pgi_file:
            _pgi_file.write("".join(_pgi_content))

    group_init = new_group_path / "__init__.py"
    if dry_run:
        group_init = old_group_path / "__init__.py"

    _gi_content = []
    with open(group_init) as _gi_file:
        for _line in _gi_file:
            _line = _line.replace(f"def {old_group_name[-1]}", f"def {new_group_name[-1]}")
            _line = _line.replace(f"{old_group_name[-1]}.add_command", f"{new_group_name[-1]}.add_command")
            _gi_content.append(_line)

    if dry_run:
        logger.info(to_header_line(f"Writing {new_group_path / '__init__.py'}"))
        logger.info("".join(_gi_content))
    else:
        logger.info(f"Writing {new_group_path / '__init__.py'}")
        with open(group_init, "w") as _gi_file:
            _gi_file.write("".join(_gi_content))

    old_depth = len(old_group_name)
    new_depth = len(new_group_name)

    depth_change = new_depth - old_depth

    if depth_change != 0:
        logger.info("Updating relative import depths to match new group organization")
        gr_path = new_group_path
        if dry_run:
            gr_path = old_group_path
        for root, _, _ in os.walk(gr_path):
            _r = pathlib.Path(root).relative_to(gr_path)

            for _f_name in glob.glob(str(pathlib.Path(root) / "*.py")):
                _f_local_path = _r / _f_name
                _f_content = []
                with open(_f_name) as _f:
                    for _line in _f:
                        if _line.startswith("from .."):
                            if depth_change > 0:
                                _line = _line[:5] + (".." * depth_change) + _line[5:]
                            elif depth_change < 0:
                                _line = _line[:5] + _line[5 - (depth_change * 2):]
                        _f_content.append(_line)
                if dry_run:
                    logger.info(to_header_line(f"Updating {new_group_path / _f_local_path}"))
                    logger.info("".join(_f_content))
                else:
                    logger.info(f"Updating {new_group_path / _f_local_path}")
                    with open(group_init, "w") as _gi_file:
                        _gi_file.write("".join(_f_content))

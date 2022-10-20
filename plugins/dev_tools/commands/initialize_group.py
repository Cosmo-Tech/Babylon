import logging
import pathlib
import shutil

from click import argument
from click import command
from click import make_pass_decorator
from click import pass_context
from click.core import Context

from Babylon.utils import TEMPLATE_FOLDER_PATH
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.string import is_valid_command_name

logger = logging.getLogger("Babylon")
pass_base_path = make_pass_decorator(pathlib.Path)


@command()
@argument("group_name", nargs=-1)
@pass_base_path
@pass_context
@timing_decorator
def initialize_group(ctx: Context, base_path: pathlib.Path, group_name: list[str]):
    """Will initialize code for GROUP_NAME and make it available

GROUP_NAME must only contain alphanumeric characters or -"""
    if any([not is_valid_command_name(n) for n in group_name]):
        logger.error(f"`{' '.join(group_name)}` contains illegal characters (only accept alphanumeric or -)")
        return

    group_name = [name.lower().replace("-", "_") for name in group_name]

    logger.debug(f"Initializing group `{' '.join(group_name)}`")
    root_group_path = base_path / "groups"
    _g_path = "/groups/".join(group_name)
    target_group_path = root_group_path / _g_path

    if target_group_path.exists():
        logger.error(f"Group `{' '.join(group_name)}` already exists")
        return
    logger.debug(f"Group `{' '.join(group_name)}` does not exists, creating it.")

    if len(group_name) > 1:
        parent_group_path = root_group_path / "/groups/".join(group_name[:-1])
        if not parent_group_path.exists():
            logger.info(
                f"Group `{' '.join(group_name[:-1])}` does not exists creating it before creating `{group_name[-1]}`.")
            ctx.invoke(initialize_group, group_name=group_name[:-1])
    else:
        parent_group_path = base_path

    template_path = TEMPLATE_FOLDER_PATH / "group_template"
    shutil.copytree(template_path, target_group_path)

    parent_group_init = parent_group_path / "groups/__init__.py"
    _pgi_content = []
    with open(parent_group_init) as _pgi_file:
        for _line in _pgi_file:
            _pgi_content.append(_line)

    _pgi_content.insert(0, f'from .{group_name[-1]} import {group_name[-1]}\n')
    _pgi_content.insert(_pgi_content.index('list_groups = [\n') + 1, f'    {group_name[-1]},\n')

    with open(parent_group_init, "w") as _pgi_file:
        _pgi_file.write("".join(_pgi_content))

    group_init = target_group_path / "__init__.py"
    _gi_content = []
    with open(group_init) as _gi_file:
        for _line in _gi_file:
            _gi_content.append(_line.replace('group_template', group_name[-1]))

    with open(group_init, "w") as _gi_file:
        _gi_file.write("".join(_gi_content))

    logger.debug(f"Group `{' '.join(group_name)}` was created")

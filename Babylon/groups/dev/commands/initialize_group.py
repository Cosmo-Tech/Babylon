import logging
import shutil

from click import argument
from click import command
from click import pass_context
from click.core import Context

from ....utils import BABYLON_PATH
from ....utils import TEMPLATE_FOLDER_PATH
from ....utils.decorators import timing_decorator
from ....utils.string import is_valid_command_name

logger = logging.getLogger("Babylon")


@command()
@argument("group_name", nargs=-1)
@pass_context
@timing_decorator
def initialize_group(ctx: Context, group_name: list[str]):
    """Will initialize code for GROUP_NAME and make it available

GROUP_NAME must only contain alphanumeric characters or -"""
    if any([not is_valid_command_name(n) for n in group_name]):
        logger.error(f"`{' '.join(group_name)}` contains illegal characters (only accept alphanumeric or -)")
        return
    group_name = [name.lower().replace("-", "_") for name in group_name]
    logger.debug(f"Initializing group `{' '.join(group_name)}`")
    babylon_groups_path = BABYLON_PATH / "groups"
    _g_path = "/groups/".join(group_name)
    group_path = babylon_groups_path / _g_path
    if group_path.exists():
        logger.error(f"Group `{' '.join(group_name)}` already exists")
        return
    logger.debug(f"Group `{' '.join(group_name)}` does not exists, creating it.")
    if len(group_name) > 1:
        parent_group_path = babylon_groups_path / "/groups/".join(group_name[:-1])
        if not parent_group_path.exists():
            logger.info(f"Group `{' '.join(group_name[:-1])}` does not exists creating it before creating `{group_name[-1]}`.")
            ctx.invoke(initialize_group, group_name=group_name[:-1])
    else:
        parent_group_path = BABYLON_PATH
    template_path = TEMPLATE_FOLDER_PATH / "group_template"
    shutil.copytree(template_path, group_path)
    parent_group_init = parent_group_path / "groups/__init__.py"
    _pgi_content = []
    with open(parent_group_init) as _pgi_file:
        for _line in _pgi_file:
            _pgi_content.append(_line)
    _pgi_content.insert(0, f'from .{group_name[-1]} import {group_name[-1]}\n')
    _pgi_content.insert(_pgi_content.index('list_groups = [\n')+1, f'    {group_name[-1]},\n')
    with open(parent_group_init, "w") as _pgi_file:
        _pgi_file.write("".join(_pgi_content))

    group_init = group_path / "__init__.py"
    _gi_content = []
    with open(group_init) as _gi_file:
        for _line in _gi_file:
            _gi_content.append(_line)
    for i in range(len(_gi_content)):
        _gi_content[i] = _gi_content[i].replace('group_template', group_name[-1])
    with open(group_init, "w") as _gi_file:
        _gi_file.write("".join(_gi_content))



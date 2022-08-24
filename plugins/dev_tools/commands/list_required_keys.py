import glob
import logging
import os
import pathlib

from click import argument
from click import command
from click import make_pass_decorator

from Babylon.utils.string import is_valid_command_name

logger = logging.getLogger("Babylon")
pass_base_path = make_pass_decorator(pathlib.PosixPath)


@command()
@pass_base_path
@argument("group_name", nargs=-1)
def list_required_keys(base_path: pathlib.Path, group_name: list[str]):
    """Check code base to list platform and deployment keys
if GROUP_NAME is defined will limit the check to the given group"""
    platform_template_keys = set()
    deployment_template_keys = set()

    if any([not is_valid_command_name(n) for n in group_name]):
        logger.error(f"`{' '.join(group_name)}` contains illegal characters (only accept alphanumeric or -)")
        return
    group_name = [name.lower().replace("-", "_") for name in group_name]
    if group_name:
        babylon_groups_path = base_path / "groups"
        _g_path = "/groups/".join(group_name)
        group_path = babylon_groups_path / _g_path
        if group_path.exists():
            base_path = group_path
        else:
            logger.error(f"Group `{' '.join(group_name)}` does not exists")
            return

    for root, _, _ in os.walk(str(base_path)):
        for _f_name in glob.glob(str(pathlib.Path(root) / "*.py")):
            with open(_f_name) as _f:
                for _line in _f:
                    if _line.startswith("@require_platform_key"):
                        key = _line.split("\"")[1]
                        platform_template_keys.add(key)
                    elif _line.startswith("@require_deployment_key"):
                        key = _line.split("\"")[1]
                        deployment_template_keys.add(key)
    if group_name:
        logger.info(f"For the group `{' '.join(group_name)}`:")
    else:
        logger.info(f"For `babylon`:")
    if platform_template_keys:
        logger.info(" -Required platform keys:")
        for k in sorted(platform_template_keys):
            logger.info("  -" + k)
    else:
        logger.info(" -No platform keys are required")
    if deployment_template_keys:
        logger.info(" -Required deployment keys:")
        for k in sorted(deployment_template_keys):
            logger.info("  -" + k)
    else:
        logger.info(" -No deployment keys are required")

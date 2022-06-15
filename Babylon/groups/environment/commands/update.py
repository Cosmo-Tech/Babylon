from click import command
from click import pass_obj
from click import argument

from ....utils.decorators import timing_decorator
from ....utils.environment import Environment

from pathlib import Path
import logging

logger = logging.getLogger("Babylon")


@command()
@argument("target")
@pass_obj
@timing_decorator
def update(ctx, target):
    """Update an environment in given TARGET folder with missing template parts"""
    file_path = Path(target)
    if file_path.is_file():
        logger.error(f"{target} is a file")
        return
    env = Environment(target, logger)
    env.check_template(update_if_error=True)

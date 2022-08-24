import logging

from click import command

from ....utils.decorators import pass_working_dir
from ....utils.decorators import timing_decorator
from ....utils.working_dir import WorkingDir

logger = logging.getLogger("Babylon")


@command()
@pass_working_dir
@timing_decorator
def init(working_dir: WorkingDir):
    """Initialize the current working_dir"""
    if working_dir.is_zip:
        logger.error("You can't initialize a zip based working_dir.")
    else:
        working_dir.copy_template()

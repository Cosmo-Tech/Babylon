import logging
from typing import Optional

from click import command
from click import option

from ....utils.decorators import pass_working_dir
from ....utils.decorators import timing_decorator
from ....utils.working_dir import WorkingDir

logger = logging.getLogger("Babylon")


@command()
@pass_working_dir
@timing_decorator
@option("-i", "--working-dir-zip", "working_dir_zip")
def init(
    working_dir: WorkingDir,
    working_dir_zip: Optional[str],
):
    """Initialize the current working_dir"""
    if working_dir.is_zip:
        logger.error("You can't initialize a zip based working_dir.")
    else:
        working_dir.copy_template()

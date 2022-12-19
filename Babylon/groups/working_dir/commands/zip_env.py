import logging

from click import argument
from click import command
from click import option

from ....utils.environment import Environment
from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@argument("path")
@option("-f", "--force", "force_overwrite", is_flag=True, help="Force replacement of existing file with new zip")
@timing_decorator
def zip_env(path, force_overwrite):
    """Zip a working_dir to given PATH

    PATH can be a folder (archive name will default to working_dir.zip) or a .zip file
    """
    working_dir = Environment().working_dir
    out = working_dir.create_zip(zip_path=path, force_overwrite=force_overwrite)
    if out:
        logger.info(f"working_dir was zipped in {out}")
    else:
        logger.error("Issues during the zipping of the working_dir.")
        if not force_overwrite:
            logger.error("Did you try using the force_overwrite option?")

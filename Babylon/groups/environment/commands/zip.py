import logging

from click import command
from click import pass_obj
from click import argument
from click import option

from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@argument("path")
@option("-f", "--force", "force_overwrite", is_flag=True, help="Force replacement of existing file with new zip")
@pass_obj
@timing_decorator
def zip_env(environment, path, force_overwrite):
    """Zip an environment to given PATH

    PATH can be a folder (archive name will default to Environment.zip) or a .zip file
    """
    out = environment.create_zip(zip_path=path, force_overwrite=force_overwrite)
    if out:
        logger.info(f"Environment was zipped in {out}")
    else:
        logger.error("Issues during the zipping of the environment.")
        if not force_overwrite:
            logger.error("Did you try using the force_overwrite option?")

from logging import getLogger
from pprint import pformat

from cosmotech_api.exceptions import UnauthorizedException
from click import argument, command, make_pass_decorator, option
from cosmotech_api.api.organization_api import OrganizationApi

from Babylon.utils.api import get_api_file
from Babylon.utils.decorators import allow_dry_run, pass_environment, timing_decorator
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)

@command()
@allow_dry_run
@pass_environment
@timing_decorator
@pass_organization_api
@argument("organization_file")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
@option(
    "-s",
    "--select",
    "select",
    type=bool,
    help="Should ...",
    required=False,
)
def create(
    env: Environment,
    organization_api: OrganizationApi,
    organization_file: str,
    use_working_dir_file: bool = False,
    select: bool = True,
    dry_run: bool = False,
):
    """Register new organization by sending a JSON or YAML file to Cosmotech Api"""

    converted_organization_content = get_api_file(
            api_file_path=organization_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
    if not converted_organization_content:
        logger.error("Error : can not get Organization definition, please check your Organization.YAML file")
        return

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.create_organization")
        retrieved_data = converted_organization_content
        retrieved_data["id"] = "<DRY RUN>"
        return
    try:
        retrieved_data = organization_api.register_organization(
            organization=converted_organization_content
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
    if select:
            env.configuration.set_deploy_var( #Possible error
                "organization_id", retrieved_data["id"]
            )
    logger.debug(pformat(retrieved_data))
    logger.info("Created new organization with id: %s", retrieved_data['id'])
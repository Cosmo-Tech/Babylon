from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api.organization_api import OrganizationApi

from Babylon.utils import TEMPLATE_FOLDER_PATH
from Babylon.utils.api import get_api_file
from Babylon.utils.decorators import allow_dry_run
from Babylon.utils.decorators import pass_environment
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)


@command()
@allow_dry_run
@timing_decorator
@pass_organization_api
@pass_environment
@argument("organization_file", required=False, type=str)
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
    help="If true, the created Organization will be set as organization of current babylon context",
    required=False,
    default=True,
)
@option(
    "-n",
    "--name",
    "organization_name",
    required=False,
    type=str,
    help="New organization name",
)
def create(
    env: Environment,
    organization_api: OrganizationApi,
    select: bool,
    dry_run: bool = False,
    organization_file: Optional[str] = None,
    use_working_dir_file: bool = False,
    organization_name: Optional[str] = None,
):
    """Register new organization by sending a JSON or YAML file to Cosmotech Api"""

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.create_organization")
        return

    if not organization_file and not organization_name:
        logger.error(
            "Error : can not get an organization name, please check your Organization.YAML file or set --name option"
        )
        return

    converted_organization_content = get_api_file(
        api_file_path=organization_file or f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Organization.yaml",
        use_working_dir_file=use_working_dir_file if organization_file else False,
        logger=logger,
    )
    if converted_organization_content is None:
        logger.error("Error : can not get Organization definition, please check your Organization.YAML file")
        return

    if organization_name and "name " not in converted_organization_content:
        converted_organization_content["name"] = organization_name

    try:
        retrieved_data = organization_api.register_organization(organization=converted_organization_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if select:
        env.configuration.set_deploy_var("organization_id", retrieved_data["id"])  # May return environnement error
    logger.debug(pformat(retrieved_data))
    logger.info("Created new organization with id: {retrieved_data['id']}")

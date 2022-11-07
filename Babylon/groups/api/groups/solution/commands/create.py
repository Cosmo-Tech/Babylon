import json
from logging import getLogger
from typing import Optional

from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import pass_environment
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@describe_dry_run("Would call **solution_api.create_solution** to register a new solution")
@timing_decorator
@pass_solution_api
@pass_environment
@argument("solution-name")
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@require_deployment_key("simulator_url", "simulator_url")
@require_deployment_key("organization_id", "organization_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
@option(
    "-i",
    "--solution-file",
    "solution_file",
    help="Your custom Solution description file path",
)
@option(
    "-d",
    "--description",
    "solution_description",
    help="New solution description",
)
@option(
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-s",
    "--select",
    "select",
    type=bool,
    help="Select this new Solution as babylon context solution ?",
    default=True,
)
def create(
    env: Environment,
    solution_api: SolutionApi,
    select: bool,
    organization_id: str,
    solution_name: str,
    simulator_url: str,
    simulator_version: str,
    simulator_repository: str,
    output_file: Optional[str] = None,
    solution_file: Optional[str] = None,
    solution_description: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
) -> Optional[str]:
    """Send a JSON or YAML file to the API to create an solution."""

    converted_solution_content = get_api_file(
        api_file_path=solution_file
        if solution_file else f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Solution.yaml",
        use_working_dir_file=use_working_dir_file if solution_file else False,
        logger=logger,
    )
    if not converted_solution_content:
        logger.error("Error : can not get correct solution definition, please check your Solution.YAML file")
        return

    if not solution_description and "solution_description" not in converted_solution_content:
        converted_solution_content["description"] = solution_name

    converted_solution_content["name"] = solution_name
    converted_solution_content["key"] = solution_name.replace(" ", "")
    converted_solution_content["version"] = simulator_version
    converted_solution_content["repository"] = simulator_repository
    converted_solution_content["url"] = simulator_url

    try:
        retrieved_solution = solution_api.create_solution(organization_id=organization_id,
                                                          solution=converted_solution_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return

    if select:
        env.configuration.set_deploy_var("solution_id", retrieved_solution["id"])

    logger.info("Created new solution with \n"
                f" - id: {retrieved_solution['id']}\n"
                f" - key: {retrieved_solution['key']}\n"
                f" - repository: {retrieved_solution['repository']}\n"
                f" - version: {retrieved_solution['version']}")

    if output_file:
        converted_content = convert_keys_case(retrieved_solution, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")

    return retrieved_solution['id']

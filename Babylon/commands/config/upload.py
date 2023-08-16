import logging
import inquirer

from ruamel.yaml import YAML
from hvac import Client
from click import Choice, command, option
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.config import config_files

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@option("-rw", "rewrite", multiple=True, type=Choice(config_files))
@option("-y", "--yes", "yes", is_flag=True, help="Automatic yes to confirm new platform registry")
@pass_hvac_client
def upload(
    hvac_client: Client,
    rewrite: list,
    yes: bool,
) -> CommandResponse:
    """
    Register or update a new configuration
    """
    yaml_loader = YAML()
    environ_id = env.environ_id
    rewrite = list(rewrite)
    platforms = hvac_client.list(path=f"{env.organization_name}/{env.tenant_id}/babylon/config/{environ_id}")
    if platforms is None and not yes:
        question = [inquirer.Confirm(name="new_platform", message="Do you want continue")]
        response = inquirer.prompt(question)
        if not response['new_platform']:
            return CommandResponse.fail()

    for o in config_files:
        section_path = env.working_dir.original_config_dir / f"{o}.yaml"
        section_data = yaml_loader.load(section_path.absolute())
        section_keys = dict(section_data).keys()
        if platforms and o in rewrite:
            logger.info(f"[{o}]")
            data = hvac_client.read(path=f"{env.organization_name}/{env.tenant_id}/babylon/config/{environ_id}/{o}")
            logger.info(f"rw {env.organization_name}/{env.tenant_id}/babylon/config/{environ_id}/{o}")
            for i in section_keys:
                if i not in data['data'].keys():
                    data['data'].update({i: section_data[i]})
            questions = [inquirer.Text(name=test, message=test, default=data['data'][test]) for test in section_keys]
            answers = inquirer.prompt(questions)
            if not answers:
                return CommandResponse.fail()
            hvac_client.write(path=f"{env.organization_name}/{env.tenant_id}/babylon/config/{environ_id}/{o}",
                              **answers)
            logger.info(f"Configuration {environ_id}/{o} successfully created")
        elif platforms and o in platforms['data']['keys']:
            logger.info(f"{env.organization_name}/{env.tenant_id}/babylon/config/{environ_id}/{o} already exists")
            continue
        else:
            logger.info(f"New path: [{o}]")
            data = dict()
            for i in section_keys:
                data.update({i: section_data[i]})
            questions = [inquirer.Text(test, message=test, default=data[test]) for test in section_keys]
            answers = inquirer.prompt(questions)
            if not answers:
                return CommandResponse.fail()
            hvac_client.write(path=f"{env.organization_name}/{env.tenant_id}/babylon/config/{environ_id}/{o}",
                              **answers)
            logger.info(f"Configuration {environ_id}/{o} successfully created")

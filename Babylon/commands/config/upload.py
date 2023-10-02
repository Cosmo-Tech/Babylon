import logging
import inquirer

from ruamel.yaml import YAML
from hvac import Client
from click import Choice, command, option
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.config import config_files

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@option("--rewrite", "rewrite", multiple=True, type=Choice(config_files), help="Config file resource")
@option("--yes", "yes", is_flag=True, help="Automatic yes to confirm new platform registry")
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

    vault_path_config = f"{env.organization_name}/{env.tenant_id}/babylon/config/{environ_id}"

    platforms = hvac_client.list(path=vault_path_config)
    if platforms is None and not yes:
        question = [inquirer.Confirm(name="new_platform", message="Do you want to continue")]
        response = inquirer.prompt(question)
        if not response['new_platform']:
            return CommandResponse.fail()

    for config_file in config_files:
        section_path = env.working_dir.original_config_dir / f"{config_file}.yaml"
        section_data = yaml_loader.load(section_path.absolute())
        section_keys = dict(section_data).keys()
        if platforms and config_file in rewrite:
            logger.info(f"[{config_file}]")
            secrets = hvac_client.read(path=f"{vault_path_config}/{config_file}")
            secrets_data = secrets["data"]
            logger.info(f"rw {vault_path_config}/{config_file}")
            for i in section_keys:
                secrets_data.setdefault(i, section_data[i])
            questions = [
                inquirer.Text(name=secret_key, message=secret_key, default=secrets_data[secret_key])
                for secret_key in section_keys
            ]
            answers = inquirer.prompt(questions)
            if not answers:
                return CommandResponse.fail()
            hvac_client.write(path=f"{vault_path_config} /{config_file}", **answers)
            logger.info(f"Configuration {environ_id}/{config_file} successfully created")
        elif platforms and config_file in platforms['data']['keys']:
            logger.info(f"{vault_path_config} / {config_file} already exists")
            continue
        else:
            logger.info(f"New path: [{config_file}]")
            new_secrets_data = dict()
            for i in section_keys:
                new_secrets_data.update({i: section_data[i]})
            questions = [
                inquirer.Text(new_key, message=new_key, default=new_secrets_data[new_key]) for new_key in section_keys
            ]
            answers = inquirer.prompt(questions)
            if not answers:
                return CommandResponse.fail()
            hvac_client.write(path=f"{vault_path_config}/{config_file}", **answers)
            logger.info(f"Configuration {environ_id}/{config_file} successfully created")

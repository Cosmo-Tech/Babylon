import logging

from click import command
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from ruamel.yaml import YAML
from Babylon.utils.messages import SUCCESS_PAYLOAD_CREATED
from Babylon.utils.response import CommandResponse
from Babylon.utils.update_section import update_section_yaml

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
def create() -> CommandResponse:
    """
    Create a worspace payload
    """
    yaml_loader = YAML()
    api_file = env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.api.yaml"
    api = yaml_loader.load(api_file)

    init_file = env.working_dir.original_template_path / "api/workspace.yaml"
    out_file = env.working_dir.payload_path / f"{env.context_id}.{env.environ_id}.workspace.yaml"
    update_section_yaml(origin_file=init_file,
                        target_file=out_file,
                        section="solution.runTemplateFilter",
                        new_value=api[env.context_id]['run_templates'])

    powerbi_file = env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.powerbi.yaml"
    powerbi = yaml_loader.load(powerbi_file)
    update_section_yaml(origin_file=out_file,
                        target_file=out_file,
                        section="webApp.options.charts.dashboardsView",
                        new_value=powerbi[env.context_id]['dashboard_view'])

    update_section_yaml(origin_file=out_file,
                        target_file=out_file,
                        section="webApp.options.charts.scenarioView",
                        new_value=powerbi[env.context_id]['scenario_view'])

    logger.info(SUCCESS_PAYLOAD_CREATED("workspace"))
    return CommandResponse.success()

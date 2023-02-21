import logging

from click import command

from ....utils.command_helper import run_command
from ....utils.response import CommandResponse
from ....utils.decorators import require_deployment_key
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("deployment_name")
@require_deployment_key("webapp_domain", required=False)
@require_deployment_key("webapp_enable_insights")
def deploy(deployment_name: str, webapp_domain: str, webapp_enable_insights: bool = False) -> CommandResponse:
    """Macro command that deploys a new webapp"""
    env = Environment()
    logger.info(f"1 - Creating static webapp resource Azure{deployment_name}WebApp...")
    r_swa = run_command(["azure", "staticwebapp", "create", f"Azure{deployment_name}WebApp", "--wait"])
    if r_swa.has_failed():
        return CommandResponse.fail()

    if webapp_domain:
        logger.info(f"1b - Adding custom domain: {webapp_domain}...")
        r_swad = run_command(
            ["azure", "staticwebapp", "custom-domain", "create", f"Azure{deployment_name}WebApp", webapp_domain])
        if r_swad.has_failed():
            return CommandResponse.fail()

    logger.info("2 - Creating App Registration...")
    r_ar = run_command(["azure", "ad", "app", "create"])
    if r_ar.has_failed():
        return CommandResponse.fail()
    app_registration_id = r_ar.data["id"]

    if webapp_enable_insights:
        logger.info("2b - Creating Application insights for Static Web App...")
        r_ins = run_command(["azure", "appinsight", "create", f"Insight{deployment_name}WebApp"])
        if r_ins.has_failed():
            return CommandResponse.fail()
        
    logger.info("3 - Downloading WebApp source code...")
    r_wadl = run_command(["webapp", "download", "webapp_src"])
    if r_wadl.has_failed():
        return CommandResponse.fail()

    logger.info("4 - Exporting WebApp configuration...")
    r_exp = run_command(["webapp", "export-config", "--use-working-dir-file", "-o", "webapp_src/config.json"])
    if r_exp.has_failed():
        return CommandResponse.fail()

    logger.info("5 - Updating WebApp workflow to read config file...")
    hostname = r_swa.data["properties"]["defaultHostname"].split(".")[0]
    workflow_file = env.working_dir.get_file(f"webapp_src/.github/workflows/azure-static-web-apps-{hostname}.yml")
    r_uwf = run_command(["webapp", "update-workflow", str(workflow_file)])
    if r_uwf.has_failed():
        return CommandResponse.fail()

    logger.info("6 - Uploading WebApp configuration and workflow files...")
    config_file = env.working_dir.get_file("webapp_src/config.json")
    r_f1 = run_command(["webapp", "upload-file", str(config_file)])
    r_f2 = run_command(["webapp", "upload-file", str(workflow_file)])
    if r_f1.has_failed() or r_f2.has_failed():
        return CommandResponse.fail()

    logger.info("7 - Creating app registration identifiers for powerBI...")
    r_pbipwd = run_command(["azure", "ad", "app", "password", "create", app_registration_id, "-n", "powerbi"])
    if r_pbipwd.has_failed():
        return CommandResponse.fail()

    logger.info("8 - Adding App user to powerBI workspace ID...")
    r_pbiws = run_command(["powerbi", "workspace", "user", "add", r_ar.data["appId"], "App", "Member"])
    if r_pbiws.has_failed():
        return CommandResponse.fail()

    logger.info("9 - Adding powerbi credentials in Static WebApp settings...")
    r_swa_stgs = run_command(["azure", "staticwebapp", "app-settings", "update", f"Azure{deployment_name}WebApp"])
    if r_swa_stgs.has_failed():
        return CommandResponse.fail()
    logger.info("WebApp deployment was successfull, please wait for workflow to finish")
    logger.info(f"WebApp data is {r_swa.data}")
    return CommandResponse.success()

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
    r_swa = run_command([
        "azure", "staticwebapp", "create", f"Azure{deployment_name}WebApp", "--use-working-dir-file", "-f",
        "webapp_details.json", "--wait"
    ])

    if webapp_domain:
        logger.info(f"1b - Adding custom domain: {webapp_domain}...")
        run_command(
            ["azure", "staticwebapp", "custom-domain", "create", f"Azure{deployment_name}WebApp", webapp_domain])

    logger.info("2 - Creating App Registration...")
    r_ar = run_command(["azure", "ad", "app", "create", "--use-working-dir-file", "-f", "app_registration.json"])
    app_registration_id = r_ar.data["id"]

    logger.info("3 - Downloading WebApp source code...")
    run_command(["webapp", "download", "--use-working-dir-file", "webapp_src"])

    logger.info("4 - Exporting WebApp configuration...")
    run_command(["webapp", "export-config", "--use-working-dir-file", "-o", "webapp_src/config.json"])

    logger.info("5 - Updating WebApp workflow to read config file...")
    hostname = r_swa.data["properties"]["defaultHostname"].split(".")[0]
    workflow_file = env.working_dir.get_file(f"webapp_src/.github/workflows/azure-static-web-apps-{hostname}.yml")
    run_command(["webapp", "update-workflow", str(workflow_file)])

    logger.info("6 - Uploading WebApp configuration and workflow files...")
    config_file = env.working_dir.get_file("webapp_src/config.json")
    run_command(["webapp", "upload-file", str(config_file)])
    run_command(["webapp", "upload-file", str(workflow_file)])

    logger.info("7 - Creating app registration identifiers for powerBI...")
    run_command(["azure", "ad", "app", "password", "create", app_registration_id, "-n", "powerbi"])

    logger.info("8 - Adding App user to powerBI workspace ID...")
    run_command(["powerbi", "workspace", "user", "add", r_ar.data["appId"], "App", "Member"])

    logger.info("9 - Adding powerbi credentials in Static WebApp settings...")
    run_command([
        "azure", "staticwebapp", "app-settings", "update", "--use-working-dir-file", "-f", "webapp_settings.json",
        f"Azure{deployment_name}WebApp"
    ])

    if webapp_enable_insights:
        logger.info("9b - Creating Application insights for Static Web App...")
        run_command([
            "azure", "appinsight", "create", f"Insight{deployment_name}WebApp", "--use-working-dir-file", "-f",
            "app_insight.json"
        ])
    return CommandResponse.success()

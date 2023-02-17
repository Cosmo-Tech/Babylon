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
    logger.setLevel(logging.DEBUG)
    # Step 1: Create static webapp resource
    r_swa = run_command([
        "azure", "staticwebapp", "create", f"Azure{deployment_name}WebApp", "--use-working-dir-file", "-f",
        "webapp_details.json"
    ])

    # Step 2: Add Custom Domain to swa
    if webapp_domain:
        run_command(
            ["azure", "staticwebapp", "custom-domain", "create", f"Azure{deployment_name}WebApp", webapp_domain])

    # Step 3: Create app registration
    r_ar = run_command(["azure", "ad", "app", "create", "--use-working-dir-file", "-f", "app_registration.json"])
    app_registration_id = r_ar.data["id"]

    # Step 4: Download webapp source code
    run_command(["webapp", "download", "webapp_src", "--use-working-dir-file"])

    # Step 5: Change webapp remote repository...
    # TODO: Add webapp command to change remote of a webapp repository

    # Step 6: Export webapp configuration
    run_command(["webapp", "export-config", "--use-working-dir-file", "-o", "webapp_src/config.json"])

    # Step 7: Update webapp workflow
    hostname = r_swa.data["properties"]["defaultHostname"].split(".")[0]
    workflow_file = env.working_dir.get_file(f"webapp_src/.github/workflows/azure-static-web-apps-{hostname}.yml")
    run_command(["webapp", "update-workflow", str(workflow_file)])

    # Step 7: Upload updated config and workflow
    config_file = env.working_dir.get_file("webapp_src/config.json")
    run_command(["webapp", "upload-file", str(config_file)])
    run_command(["webapp", "upload-file", str(workflow_file)])

    # Step 8: Create an App Registration secret for powerbi
    run_command(["azure", "ad", "app", "password", "create", app_registration_id, "-n", "powerbi"])

    # Step 9: Add App Registration as member of powerbi workspace
    run_command(["powerbi", "workspace", "user", "add", app_registration_id, "App", "Member"])

    # Step 10: Update static webapp settings with powerbi credentials
    run_command(["azure", "staticwebapp", "app_settings", "update", "--use-working-dir-file", "webapp_settings.json"])

    # Create Application insight
    if webapp_enable_insights:
        run_command([
            "azure", "appinsight", "create", f"Insight{deployment_name}WebApp", "--use-working-dir-file", "-f",
            "app_insight.json"
        ])

import logging

from click import command
from click import option

from ....utils.command_helper import run_command
from ....utils.response import CommandResponse
from ....utils.decorators import require_deployment_key
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("deployment_name")
@require_deployment_key("webapp_domain", required=False)
@option("--enable_insight"
        "enable_insight", is_flag=True, help="Should the webapp have an app insight ?")
def deploy(deployment_name: str, webapp_domain: str, enable_insight: bool = False) -> CommandResponse:
    """Macro command that deploys a new webapp"""
    env = Environment()
    # Step 1: Create static webapp resource
    r_swa = run_command([
        "azure", "staticwebapp", "create", f"Azure{deployment_name}WebApp", "--use-working-dir-file", "-f",
        "webapp_details.json"
    ])

    # Step 2: Add Custom Domain to swa
    if webapp_domain:
        run_command(
            ["azure", "staticwebapp", "custom_domain", "create", f"Azure{deployment_name}WebApp", webapp_domain])

    # Step 3: Create app registration
    r_ar = run_command(["azure", "ad", "app", "create", "--use-working-dir-file", "app_registration.json"])
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
    run_command(["webapp", "update-workflow", workflow_file])

    # Step 7: Upload updated config and workflow
    config_file = env.working_dir.get_file("webapp_src/config.json")
    run_command(["webapp", "upload_file", config_file])
    run_command(["webapp", "upload_file", workflow_file])

    # Step 8: Create an App Registration secret for powerbi
    r_pbi = run_command(["ad", "app", "password", "create", app_registration_id, "-n", "powerbi"])

    # Step 9: Add App Registration as member of powerbi workspace
    run_command(["powerbi", "workspace", "user", "add", app_registration_id, "App", "Member"])

    # Step 10: Update static webapp settings with powerbi credentials
    run_command(["azure", "staticwebapp", "app_settings", "update", "--use-working-dir-file", "webapp_settings.json"])

    # Create Application insight
    if enable_insight:
        run_command([
            "azure", "appinsight", "create", f"Insight{deployment_name}WebApp", "--use-working-dir-file", "-f",
            "app_insight.json"
        ])

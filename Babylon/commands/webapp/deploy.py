import logging
from pathlib import Path

from click import command
from click import option

from ...utils.decorators import require_deployment_key
from ...utils.decorators import require_platform_key
from ...utils.macro import Macro

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("deployment_name")
@require_platform_key("azure_powerbi_group_id")
@require_deployment_key("webapp_domain", required=False)
@require_deployment_key("webapp_enable_insights")
@option("--enable-powerbi", "enable_powerbi", is_flag=True, help="Enable PowerBI configuration")
def deploy(deployment_name: str,
           azure_powerbi_group_id: str,
           webapp_domain: str,
           webapp_enable_insights: bool = False,
           enable_powerbi: bool = False):
    """Macro command that deploys a new webapp"""
    m = Macro("webapp deploy") \
        .step(["azure", "staticwebapp", "create", f"Azure{deployment_name}WebApp"], store_at="webapp") \
        .then(
            lambda m: m.env.convert_data_query("%datastore%webapp.data.properties.defaultHostname").split(".")[0],
            store_at="hostname") \
        .step(
            ["azure", "staticwebapp", "custom-domain", "create", f"Azure{deployment_name}WebApp", webapp_domain],
            is_required=False) \
        .step(["azure", "ad", "app", "create"], store_at="app") \
        .step(
            ["azure", "appinsight", "create", f"Insight{deployment_name}WebApp"],
            store_at="insights", run_if=webapp_enable_insights) \
        .step(["config", "set-variable", "deploy", "webapp_insights_instrumentation_key",
               "%datastore%insights.properties.InstrumentationKey"], run_if=webapp_enable_insights) \
        .step(
            ["azure", "ad", "group", "member", "add", azure_powerbi_group_id, "%datastore%app.data.id"],
            is_required=False, run_if=enable_powerbi)

    # Wait for workflow file to be created by static webapp
    workflow_file = ("webapp_src/.github/workflows/azure-static-web-apps-"
                     f"{m.env.convert_data_query('%datastore%hostname')}.yml")
    while not Path(workflow_file).exists():
        m.step(["webapp", "download", "webapp_src"])

    m.step(["webapp", "export-config", "-o", "webapp_src/config.json"]) \
        .step(["webapp", "update-workflow", workflow_file]) \
        .step(["webapp", "upload-file", "webapp_src/config.json"]) \
        .step(["webapp", "upload-file", "webapp_src/.github/workflows/"]) \
        .step(
            ["azure", "ad", "app", "password", "create", "%datastore%app.data.id", "-n", "powerbi"],
            run_if=enable_powerbi) \
        .step(
            ["powerbi", "workspace", "user", "add", "%datastore%app.data.appId", "App", "Member"],
            run_if=enable_powerbi) \
        .step(
            ["azure", "staticwebapp", "app-settings", "update", f"Azure{deployment_name}WebApp"],
            run_if=enable_powerbi) \
        .dump("webapp_deploy.json")

import logging
from pathlib import Path
import pathlib

from click import argument, command
from click import option

from Babylon.utils.typing import QueryType

from ...utils.decorators import require_deployment_key
from ...utils.decorators import require_platform_key
from ...utils.macro import Macro

logger = logging.getLogger("Babylon")


@command()
@require_platform_key("azure_powerbi_group_id")
@require_deployment_key("deployment_name")
@require_deployment_key("webapp_domain", required=False)
@require_deployment_key("webapp_enable_insights")
@option("--enable-powerbi", "enable_powerbi", is_flag=True, help="Enable PowerBI configuration")
@option("--enable-azfunc", "enable_azfunc", is_flag=True, help="Enable Azure Function configuration")
@option("--azfunc-path", "azfunc_path", type=QueryType(), default="")
def deploy(deployment_name: str,
           azure_powerbi_group_id: str,
           webapp_domain: str,
           azfunc_path: str,
           webapp_enable_insights: bool = False,
           enable_powerbi: bool = False,
           enable_azfunc: bool = False):
    """Macro command that deploys a new webapp"""
    m = Macro("webapp deploy") \
        .step(["azure", "staticwebapp", "create", f"Azure{deployment_name}WebApp"], store_at="webapp") \
        .then(
            lambda m: m.env.convert_data_query("%datastore%webapp.data.properties.defaultHostname").split(".")[0],
            store_at="hostname") \
        .step(["config", "set-variable", "deploy", "webapp_static_domain", "%datastore%webapp.data.properties.defaultHostname"]) \
        .step(["azure", "staticwebapp", "get", f"Azure{deployment_name}WebApp"]) \
        .step(["azure", "ad", "app", "create", f"Azure{deployment_name}WebApp"], store_at="app") \
        .step(["azure", "ad", "app", "get", "%datastore%app.data.id"]) \
        .step(
            ["azure", "ad", "app", "password", "create", "%datastore%app.data.id", "-n", "powerbi", "-s"],
            run_if=enable_powerbi) \
        .step(
            ["azure", "ad", "app", "password", "create", "%datastore%app.data.id", "-n", "functionapp", "--azf"],
            run_if=enable_azfunc) \
        .step(["config", "set-variable", "deploy", "webapp_registration_id", "%datastore%app.data.appId"]) \
        .step(["config", "set-variable", "deploy", "webapp_principal_id", "%datastore%app.data.id"]) \
        .step(["azure", "arm", "runtmp", "-f", azfunc_path], run_if=enable_azfunc) \
        .step(
            ["azure", "staticwebapp", "custom-domain", "create", f"Azure{deployment_name}WebApp", webapp_domain],
            is_required=False) \
        .step(
            ["azure", "appinsight", "create", f"Insight{deployment_name}WebApp"],
            store_at="insights", run_if=webapp_enable_insights) \
        .step(["config", "set-variable", "deploy", "webapp_insights_instrumentation_key",
               "%datastore%insights.properties.InstrumentationKey"], run_if=webapp_enable_insights) \
        .step(
            ["azure", "staticwebapp", "app-settings", "update", f"Azure{deployment_name}WebApp"],
            run_if=enable_powerbi) \
        .step(
            ["azure", "ad", "group", "member", "add", "-gi", azure_powerbi_group_id, "-pi", "%datastore%app.data.servicePrincipalId"],
            is_required=False, run_if=enable_powerbi)

    # Wait for workflow file to be created by static webapp
    workflow_file = ("webapp_src/.github/workflows/azure-static-web-apps-"
                     f"{m.env.convert_data_query('%datastore%hostname')}.yml")
    timeout = 0
    while not Path(workflow_file).exists() and timeout < 20:
        m.wait(2) \
            .step(["webapp", "download", "webapp_src"])
        timeout += 2
    m.step(["webapp", "export-config", "-o", "webapp_src/config.json"]) \
        .step(["webapp", "update-workflow", workflow_file]) \
        .step(["webapp", "upload-many", "-f", "webapp_src/config.json", "-f", "webapp_src/.github/workflows/"]) \
        .step(
            ["powerbi", "workspace", "user", "add", "%datastore%app.data.servicePrincipalId", "App", "Member"],
            run_if=enable_powerbi) \
        .dump("webapp_deploy.json")
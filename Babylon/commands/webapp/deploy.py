import logging

from pathlib import Path
import pathlib
import sys
from typing import Any, Optional
from click import command
from click import option
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.macro import Macro

logger = logging.getLogger("Babylon")
env = Environment()

prefixWebApp = "WebApp"
prefixApp = "App"


@command()
@wrapcontext
@option("--arm-path", "arm_path", type=pathlib.Path, help="Your custom arm azure function description file yaml")
@inject_context_with_resource({'webapp': ['enable_insights', 'deployment_name'], 'powerbi': ['group_id']})
def deploy(context: Any, arm_path: Optional[pathlib.Path] = None):
    """
    Macro command that deploys a new webapp
    """
    deployment_name = context['webapp_deployment_name']
    azure_powerbi_group_id = context["powerbi_group_id"]
    github_secret = env.get_global_secret(resource="github", name="token")
    if not github_secret:
        logger.error("Personal Access Token Github not found")
        sys.exit(1)

    macro = Macro("webapp deploy").step(["azure", "staticwebapp", "get", f'{prefixWebApp}{deployment_name}'],
                                        store_at="webapp")
    if not macro.env.get_data_from_store(["webapp", "id"]):
        macro = macro.step(["azure", "staticwebapp", "create", f"{prefixWebApp}{deployment_name}"]).wait(5)
    else:
        logger.info("The webapp already exists")
        sys.exit(1)

    macro = macro.step(["azure", "ad", "app", "get-all"], store_at="apps")
    apps = macro.env.get_data_from_store(["apps"])
    created = False
    for i in apps:
        name = i['displayName']
        if f"{prefixApp}{deployment_name}" in name:
            created = True
            logger.info("The app already exists")
            sys.exit(1)

    if not created:
        macro = macro.step(["azure", "ad", "app", "create", f"{prefixApp}{deployment_name}"])
    macro = macro.step(["azure", "ad", "app", "password", "create", "--name",
                        "azf"]).step(["azure", "ad", "app", "password", "create", "--name",
                                      "pbi"]).step(["azure", "ad", "app", "get-principal", "%app%object_id"]).step([
                                          "azure", "ad", "group", "member", "add", "--gi", azure_powerbi_group_id,
                                          "--pi", "%app%principal_id"
                                      ])

    cmd_line = ["azure", "func", "deploy", f"Arm{deployment_name}"]
    if arm_path:
        cmd_line = [*cmd_line, "--file", str(arm_path)]
    macro = macro.step(cmd_line)

    macro = macro.step(["azure", "staticwebapp", "app-settings", "update", f"WebApp{deployment_name}"])
    macro = macro.step(["github", "runs", "get", "%webapp%hostname"])
    macro = macro.step(["github", "runs", "cancel"])

    workflow_file = f'webapp_src/{macro.env.configuration.get_var("github", "workflow_path")}'
    timeout = 0
    while not Path(workflow_file).exists() and timeout < 10:
        macro.wait(2).step(["webapp", "download", "webapp_src"])
        timeout += 2

    macro.step(["webapp", "export-config", "--output", "webapp_src/config.json"]).step([
        "webapp", "update-workflow", workflow_file
    ]).step(["webapp", "upload-many", "--file", "webapp_src/config.json", "--file", "webapp_src/.github/workflows/"])

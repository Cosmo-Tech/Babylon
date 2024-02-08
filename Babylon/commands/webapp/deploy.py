import logging

from pathlib import Path
import pathlib
import sys
from typing import Any, Optional
from click import command
from click import option
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import (
    retrieve_state,
    wrapcontext,
)
from Babylon.utils.macro import Macro

logger = logging.getLogger("Babylon")
env = Environment()

prefixWebApp = "WebApp"
prefixApp = "App"


@command()
@wrapcontext()
@option(
    "--arm-path",
    "arm_path",
    type=pathlib.Path,
    help="Your custom arm azure function description file yaml",
)
@option(
    "--with-azf",
    "with_azf",
    is_flag=True,
    help="Deploy webapp with azure function",
    show_default=True,
)
@retrieve_state
def deploy(state: Any, with_azf: bool, arm_path: Optional[pathlib.Path] = None):
    """
    Macro command that deploys a new webapp
    """
    deployment_name = state["webapp_deployment_name"]
    azure_powerbi_group_id = state["powerbi_group_id"]
    github_secret = env.get_global_secret(resource="github", name="token")
    if not github_secret:
        logger.error("Personal Access Token Github is missing")
        sys.exit(1)

    macro = Macro("webapp deploy").step(
        [
            "azure",
            "staticwebapp",
            "get",
            f"{prefixWebApp}{deployment_name}",
            "-c",
            env.context_id,
            "-p",
            env.environ_id,
        ],
        store_at="webapp",
    )
    if not macro.env.get_data_from_store(["webapp", "id"]):
        macro = macro.step(
            [
                "azure",
                "staticwebapp",
                "create",
                f"{prefixWebApp}{deployment_name}",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
            ]
        ).wait(5)
    else:
        logger.info("The webapp already exists")
        sys.exit(1)

    macro = macro.step(
        ["azure", "ad", "app", "get-all", "-c", env.context_id, "-p", env.environ_id],
        store_at="apps",
    )
    apps = macro.env.get_data_from_store(["apps"])
    created = False
    for i in apps:
        name = i["displayName"]
        if f"{prefixApp}{deployment_name}" in name:
            created = True
            logger.info("The app already exists")
            sys.exit(1)

    if not created:
        macro = macro.step(
            [
                "azure",
                "ad",
                "app",
                "create",
                f"{prefixApp}{deployment_name}",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
            ]
        )
    macro = (
        macro.step(
            [
                "azure",
                "ad",
                "app",
                "password",
                "create",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
                "--name",
                "azf",
            ]
        )
        .step(
            [
                "azure",
                "ad",
                "app",
                "password",
                "create",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
                "--name",
                "pbi",
            ]
        )
        .step(
            [
                "azure",
                "ad",
                "app",
                "get-principal",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
                "%app%object_id",
            ]
        )
        .step(
            [
                "azure",
                "ad",
                "group",
                "member",
                "add",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
                "--group-id",
                azure_powerbi_group_id,
                "--principal-id",
                "%app%principal_id",
            ]
        )
    )

    if with_azf:
        cmd_line = [
            "azure",
            "func",
            "deploy",
            f"Arm{deployment_name}",
            "-c",
            env.context_id,
            "-p",
            env.environ_id,
        ]
        if arm_path:
            cmd_line = [*cmd_line, "--file", str(arm_path)]
        macro = macro.step(cmd_line)

    macro = macro.step(
        [
            "azure",
            "staticwebapp",
            "app-settings",
            "update",
            f"WebApp{deployment_name}",
            "-c",
            env.context_id,
            "-p",
            env.environ_id,
        ]
    )
    macro = macro.step(
        [
            "github",
            "runs",
            "get",
            "-c",
            env.context_id,
            "-p",
            env.environ_id,
            "%webapp%hostname",
        ]
    )
    macro = macro.step(
        ["github", "runs", "cancel", "-c", env.context_id, "-p", env.environ_id]
    )

    workflow_file = (
        f'webapp_src/{macro.env.configuration.get_var("github", "workflow_path")}'
    )
    timeout = 0
    while not Path(workflow_file).exists() and timeout < 10:
        macro.wait(2).step(
            [
                "webapp",
                "download",
                "webapp_src",
                "-c",
                env.context_id,
                "-p",
                env.environ_id,
            ]
        )
        timeout += 2

    macro.step(
        [
            "webapp",
            "export-config",
            "-c",
            env.context_id,
            "-p",
            env.environ_id,
            "--output",
            "webapp_src/config.json",
        ]
    ).step(
        [
            "webapp",
            "update-workflow",
            workflow_file,
            "-c",
            env.context_id,
            "-p",
            env.environ_id,
        ]
    ).step(
        [
            "webapp",
            "upload-many",
            "-c",
            env.context_id,
            "-p",
            env.environ_id,
            "--file",
            "webapp_src/config.json",
            "--file",
            "webapp_src/.github/workflows/",
        ]
    )

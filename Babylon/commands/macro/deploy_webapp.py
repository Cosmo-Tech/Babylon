import os
import sys
from logging import getLogger

from click import echo, style

from Babylon.commands.macro.helpers.webapp import dict_to_tfvars, ensure_tf_webapp_version, run_terraform_process
from Babylon.commands.macro.init import _TF_WEBAPP_DEFAULT_VERSION
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def deploy_webapp(namespace: str, file_content: str):
    echo(style(f"\n🚀 Deploying webapp in namespace: {env.environ_id}", bold=True, fg="cyan"))

    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload", {})
    tf_dir = env.working_dir.template_path.parent / "terraform-webapp"
    tfvars_path = tf_dir / "terraform.tfvars"

    tf_webapp_version: str = payload.pop("tf_webapp_version", None) or _TF_WEBAPP_DEFAULT_VERSION
    logger.info(f"  [dim]→ Using terraform-webapp version [cyan]{tf_webapp_version}[/cyan][/dim]")

    # Ensure the local clone is on the requested version before Terraform runs.
    if tf_dir.exists():
        ensure_tf_webapp_version(tf_dir, tf_webapp_version)
    else:
        logger.warning(
            f"  [yellow]⚠[/yellow] terraform-webapp directory not found at {tf_dir} run 'babylon init' first or clone it manually"
        )

    OS_CONFIGS = {
        "win32": {
            "script": "_run-terraform.ps1",
            "exec": lambda s: ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", f"./{s}", "--apply"],
        },
        "linux": {
            "script": "_run-terraform.sh",
            "exec": lambda s: ["/bin/bash", f"./{s}", "--apply"],
        },
    }
    config = OS_CONFIGS.get(sys.platform)
    if not config:
        raise RuntimeError(f"Unsupported operating system: {sys.platform}")

    script_name = config["script"]
    script_path = tf_dir / script_name
    executable = config["exec"](script_name)

    if not script_path.exists():
        logger.error(f"  [bold red]✘[/bold red] Script not found at {script_path}")
        return

    if sys.platform == "linux":
        os.chmod(script_path, 0o700)

    try:
        tfvars_path.write_text(dict_to_tfvars(payload))
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Failed to write tfvars: {e}")
        return

    logger.info("  [dim]→ Running Terraform deployment...[/dim]")
    run_terraform_process(executable, tf_dir, payload, state)

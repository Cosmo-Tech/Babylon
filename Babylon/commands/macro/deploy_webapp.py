import os
import sys
from logging import getLogger
from re import MULTILINE, sub

from click import echo, style

from Babylon.commands.macro.deploy import _run_terraform_process, dict_to_tfvars
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

    OS_CONFIGS = {
        "win32": {
            "script": "_run-terraform.ps1",
            "exec": lambda s: ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", f"./{s}"],
        },
        "linux": {"script": "_run-terraform.sh", "exec": lambda s: ["/bin/bash", f"./{s}"]},
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
    try:
        content = script_path.read_text()
        updated_content = sub(r"^#\s*(terraform apply.*)", r"\1", content, flags=MULTILINE)

        if content != updated_content:
            script_path.write_text(updated_content)
            if sys.platform == "linux":
                os.chmod(script_path, 0o755)
    except IOError as e:
        logger.error(f"  [bold red]✘[/bold red] Script modification failed: {e}")
        return

    try:
        tfvars_path.write_text(dict_to_tfvars(payload))
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Failed to write tfvars: {e}")
        return

    logger.info("  [dim]→ Running Terraform deployment...[/dim]")
    _run_terraform_process(executable, tf_dir, payload, state)

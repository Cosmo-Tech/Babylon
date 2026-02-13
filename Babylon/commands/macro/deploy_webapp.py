import os
import subprocess
import sys
from logging import getLogger

from click import echo, style

from Babylon.commands.macro.deploy import dict_to_tfvars
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def deploy_webapp(namespace: str, file_content: str):
    echo(style(f"\n🚀 Deploying webapp in namespace: {env.environ_id}", bold=True, fg="cyan"))

    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload", {})
    current_os = sys.platform
    tf_dir = env.working_dir.template_path.parent / "terraform-webapp"
    tfvars_path = tf_dir / "terraform.tfvars"

    if current_os == "win32":
        script_name = "_run-terraform.ps1"
        executable = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", f"./{script_name}"]
    elif current_os == "linux":
        script_name = "_run-terraform.sh"
        executable = ["/bin/bash", f"./{script_name}"]
        if (tf_dir / script_name).exists():
            os.chmod(tf_dir / script_name, 0o755)
    else:
        raise RuntimeError(f"  Unsupported operating system: {current_os}")

    script_path = tf_dir / script_name

    if not script_path.exists():
        logger.error(f"  [bold red]✘[/bold red]Script not found at {script_path}")
        return
    try:
        hcl_content = dict_to_tfvars(payload)
        with open(tfvars_path, "w") as f:
            f.write(hcl_content)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Failed to write tfvars: {e}")
        return
    logger.info("  [dim]→ Running Terraform deployment...[/dim]")
    try:
        process = subprocess.Popen(executable, cwd=tf_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line:
                continue
            if any(key in clean_line for key in ["Initializing", "Upgrading", "Finding", "Refreshing"]):
                echo(style(f"   {clean_line}", fg="white"))
            elif any(key in clean_line for key in ["Success", "complete", "Resources:"]):
                echo(style(f"   {clean_line}", fg="green"))
            elif "Error" in clean_line or "error" in clean_line:
                echo(style(f"   {clean_line}", fg="red", bold=True))
            else:
                echo(style(f"   {clean_line}", fg="white"))
        return_code = process.wait()
        webapp_name = payload.get("webapp_name")
        cluster_domain = payload.get("cluster_domain")
        tenant_name = payload.get("tenant")
        webapp_url = f"https://{cluster_domain}/{tenant_name}/webapp-{webapp_name}"
        services = state.get("services", {})
        if "webapp" not in services:
            services["webapp"] = {}
        services["webapp"]["webapp_name"] = f"webapp-{webapp_name}"
        services["webapp"]["webapp_url"] = webapp_url
        if return_code == 0:
            logger.info(f"  [bold green]✔[/bold green] WebApp [bold white]{webapp_name}[/bold white] deployed successfully")
            env.store_state_in_local(state)
            if env.remote:
                env.store_state_in_cloud(state)
        else:
            logger.error(f"  [bold red]✘[/bold red] Deployment failed with exit code {return_code}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Execution error: {e}")

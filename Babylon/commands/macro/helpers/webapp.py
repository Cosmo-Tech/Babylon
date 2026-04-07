"""
Terraform helpers for WebApp deployment and teardown.

Covers:
- Converting a payload dict to Terraform HCL tfvars format
- Running a Terraform subprocess and streaming its output
- Finalising state after a successful Terraform apply
- Destroying WebApp infrastructure via Terraform
"""

import subprocess
from logging import getLogger
from pathlib import Path
from sys import exit

from click import echo, style

from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def dict_to_tfvars(payload: dict) -> str:
    """Convert a dictionary to Terraform HCL tfvars format (key = "value").

    Currently handles simple data structures:
    - Booleans: converted to lowercase (true/false)
    - Numbers: integers and floats as-is
    - Strings: wrapped in double quotes

    Note: Complex nested structures (lists, dicts) are not yet supported.
    This is sufficient for current WebApp tfvars which only use simple scalar values.

    Args:
        payload (dict): Dictionary with simple key-value pairs

    Returns:
        str: Terraform HCL formatted variable assignments
    """
    lines = []
    for key, value in payload.items():
        if isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")
        else:
            lines.append(f'{key} = "{value}"')
    return "\n".join(lines)


def _finalize_deployment(payload: dict, state: dict) -> None:
    """Update state with the final WebApp name and URL after a successful Terraform apply."""
    webapp_name = payload.get("webapp_name")
    url = f"https://{payload.get('cluster_name')}.{payload.get('domain_zone')}/tenant-{payload.get('tenant')}/webapp-{webapp_name}"

    services = state.setdefault("services", {})
    services["webapp"] = {"webapp_name": f"webapp-{webapp_name}", "webapp_url": url}

    logger.info(f"  [bold green]✔[/bold green] WebApp [bold white]{webapp_name}[/bold white] deployed")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_kubernetes(state)


def run_terraform_process(executable: list[str], cwd, payload: dict, state: dict) -> None:
    """Stream a Terraform subprocess and finalize state on success.

    Args:
        executable: The command + arguments to run (e.g. ``['/bin/bash', './_run-terraform.sh']``).
        cwd: Working directory for the subprocess (path to the Terraform directory).
        payload: The WebApp payload dict, forwarded to ``_finalize_deployment``.
        state: Current Babylon state dict, forwarded to ``_finalize_deployment``.
    """
    try:
        process = subprocess.Popen(executable, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        # Color mapping to avoid if/else statements in the loop
        status_colors = {
            "Initializing": "white",
            "Upgrading": "white",
            "Finding": "white",
            "Refreshing": "white",
            "Success": "green",
            "complete": "green",
            "Resources:": "green",
            "Error": "red",
            "error": "red",
        }

        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line:
                continue

            color = next((status_colors[k] for k in status_colors if k in clean_line), "white")
            is_bold = color == "red"
            echo(style(f"   {clean_line}", fg=color, bold=is_bold))
            if "Error" in clean_line or "error" in clean_line:
                exit(1)

        if process.wait() == 0:
            _finalize_deployment(payload, state)
        else:
            logger.error("  [bold red]✘[/bold red] Deployment failed")

    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Execution error: {e}")


# ---------------------------------------------------------------------------
# WebApp teardown (used by destroy)
# ---------------------------------------------------------------------------


def destroy_webapp(state: dict) -> None:
    """Run Terraform destroy to tear down WebApp infrastructure."""
    logger.info("  [dim]→ Running Terraform destroy for WebApp resources...[/dim]")

    tf_dir = Path(str(env.working_dir)).parent / "terraform-webapp"

    if not tf_dir.exists():
        logger.warning(f"  [yellow]⚠[/yellow] [dim]Terraform directory not found at {tf_dir} skipping WebApp destroy[/dim]")
        return

    # --- Check Terraform state, not Babylon state ---
    tf_state_file = tf_dir / ".terraform" / "terraform.tfstate"
    if not tf_state_file.exists():
        logger.warning("  [yellow]⚠[/yellow] [dim]No terraform state found, skipping WebApp destroy[/dim]")
        return

    webapp_name = state.get("services", {}).get("webapp", {}).get("webapp_name") or "<unknown>"

    try:
        process = subprocess.Popen(
            ["terraform", "destroy", "-auto-approve", "-lock=false", "-input=false"],
            cwd=tf_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        line_handlers = {
            "Destroy complete!": "green",
            "Resources:": "green",
            "Error": "red",
        }

        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line:
                continue
            color = next((color for key, color in line_handlers.items() if key in clean_line), "white")
            bold = color == "red"
            echo(style(f"   {clean_line}", fg=color, bold=bold))

        process.wait()
        if process.returncode == 0:
            state.setdefault("services", {}).setdefault("webapp", {})
            state["services"]["webapp"]["webapp_name"] = ""
            state["services"]["webapp"]["webapp_url"] = ""
            logger.info(f"   [green]✔[/green] WebApp [magenta]{webapp_name}[/magenta] destroyed")
        else:
            logger.error(f"  [bold red]✘[/bold red] Terraform destroy failed (Code {process.returncode})")

    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Error during WebApp destruction: {e}")

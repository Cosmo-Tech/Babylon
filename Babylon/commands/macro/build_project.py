import os
import subprocess
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from io import BytesIO
from logging import getLogger
from urllib.parse import urlparse
from urllib.request import url2pathname

import git
from click import echo, style
from cosmotech_modeling_api import ApiClient, Configuration, ProjectApi, ProjectBuildApi
from cosmotech_modeling_api.models.project_build_request import ProjectBuildRequest
from cosmotech_modeling_api.models.project_request import ProjectRequest

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


class TemporaryModelingAPIProject:
    def __init__(self, project_api_instance: ProjectApi):
        self._project_api_instance = project_api_instance

    def __enter__(self):
        echo(style("  → Creating temporary project...", dim=True))
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        project_request = ProjectRequest(name=f"Babylon project - {now}", description=f"Automatic project created by babylon at {now}")
        self.id = self._project_api_instance.create_project(project_request).id
        logger.info(f"  [bold green]✔[/bold green] Created project [bold cyan]{self.id}[/bold cyan]")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info("  [dim]→ Removing temporary project[/dim]")
        self._project_api_instance.delete_project(project_id=self.id)


class ModelingBuildLogger:
    def __init__(self, build_api_instance: ProjectBuildApi, project_id: str, build_id: str):
        self._build_api_instance = build_api_instance
        self._project_id = project_id
        self._build_id = build_id
        self._previous_logs = str()

    def update_logs(self):
        new_logs = self._build_api_instance.get_project_build_logs(project_id=self._project_id, build_id=self._build_id)

        diff_logs = new_logs.removeprefix(self._previous_logs).removesuffix("\n")
        if len(diff_logs):
            logger.debug(diff_logs)

        self._previous_logs = new_logs

    def error_logs(self):
        logger.error(self._previous_logs)


# Once the modeling api is publicly exposed we should be able to remove the port-forward workaround
# and just get the target url in the babylon config instead of the service name
class ModelingAPIPortForward:
    def __enter__(self):
        pf_target = env.retrieve_config().get("modeling_api_pf")
        pf_command = ["kubectl"]
        if env.kube_context:
            pf_command += ["--context", env.kube_context]
        pf_command += ["port-forward", "--namespace", env.environ_id, pf_target, ":http"]
        echo(style(f"  → Opening port-forward to {pf_target}...", dim=True))
        self._process = subprocess.Popen(pf_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in self._process.stdout:
            if line.startswith("Forwarding from"):
                self.local_port = line.split(":")[-1].split(" ")[0]
                break
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        echo(style("  → Closing port-forward", dim=True))
        self._process.terminate()
        self._process.wait()


def _get_archive_data(archive_url: str) -> bytes | str:
    echo(style("  → Preparing project archive...", dim=True))
    project_archive_parsed_url = urlparse(archive_url)
    match project_archive_parsed_url.scheme:
        case "file":
            archive_path = url2pathname(project_archive_parsed_url.path)
            if os.path.isdir(archive_path):
                echo(style(f"  → Using folder as project archive: {archive_path}", dim=True))
                archive_io = BytesIO()
                with tarfile.open(fileobj=archive_io, mode="x:gz") as archive_tar:
                    archive_tar.add(archive_path, ".")
                archive_data = archive_io.getvalue()
            else:
                echo(style(f"  → Using file as project archive: {archive_path}", dim=True))
                archive_data = archive_path
        case scheme if scheme.startswith("git+") or scheme == "":  # empty scheme means scp variant of the git ssh protocol
            echo(style(f"  → Using git project archive: {archive_url}", dim=True))
            path_and_ref = url2pathname(project_archive_parsed_url.path).split(sep="@")
            git_ref = "main" if len(path_and_ref) < 2 else path_and_ref[-1]
            git_remote = (
                project_archive_parsed_url.path if project_archive_parsed_url.scheme == "" else archive_url.removeprefix("git+")
            )
            git_remote = git_remote.removesuffix(f"@{git_ref}")
            with tempfile.TemporaryDirectory() as git_clone_dir:
                git_clone = git.Repo.clone_from(url=git_remote, to_path=git_clone_dir, branch=git_ref, depth=1)
                archive_io = BytesIO()
                git_clone.archive(ostream=archive_io, treeish=git_ref, format="tgz", prefix="archive/", stdout_as_string=False)
                archive_data = archive_io.getvalue()
        case _:
            logger.error(f"  [bold red]✘[/bold red] Unrecognized project archive url scheme: '{archive_url}'")
            return CommandResponse.fail()
    logger.info("  [bold green]✔[/bold green] Project archive is ready")
    return archive_data


def build_project(namespace: str, file_content: str):
    echo(style(f"🚀 Building CoSML project in namespace: {env.environ_id}", bold=True, fg="cyan"))

    # Retrieve the state
    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)

    # Prepare the archive before creating the project
    archive_data = _get_archive_data(content.get("spec", {}).get("sidecars", {}).get("project", {}).get("archive_url"))

    with ModelingAPIPortForward() as api_port_forward:
        # API client initialization
        base_client = ApiClient(Configuration(host=f"http://localhost:{api_port_forward.local_port}"))
        project_api_instance = ProjectApi(base_client)
        build_api_instance = ProjectBuildApi(base_client)

        # Use a temporary project
        with TemporaryModelingAPIProject(project_api_instance) as project:
            # Upload archive
            echo(style("  → Uploading project archive...", dim=True))
            project_api_instance.upload_project_archive(project_id=project.id, body=archive_data)
            logger.info("  [bold green]✔[/bold green] Upload complete")

            # Trigger build
            payload = content.get("spec", {}).get("payload", {})
            project_build_request = ProjectBuildRequest.from_dict(payload or {})
            if not project_build_request:
                return CommandResponse.fail()
            build = build_api_instance.build_project(project_id=project.id, project_build_request=project_build_request)

            # Wait for build completion
            logger.info(f"  [dim]→ Build [bold cyan]{build.id}[/bold cyan] is running...[/dim]")
            while build_api_instance.get_project_build(project_id=project.id, build_id=build.id).status.phase not in [
                "Successful",
                "Failed",
            ]:
                time.sleep(5)

            # Build results
            build_status = build_api_instance.get_project_build(project_id=project.id, build_id=build.id).status
            build_logs = build_api_instance.get_project_build_logs(project_id=project.id, build_id=build.id)
            if build_status.phase == "Successful":
                logger.debug(build_logs)
                logger.info("  [bold green]✔[/bold green] Build success")
            else:
                logger.error(build_logs)
                logger.error(f"  [bold red]✘[/bold red] Build failed: {build_status.message}")
                return CommandResponse.fail()

    echo(style("  ✔ Build process complete", fg="green", bold=True))

import pathlib
import sys
import click
import logging

from pathlib import Path
from click import argument, command
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()

# def check(data: dict, keys: list) -> bool:
#     flat_data = flatten(data, separator=".")
#     for k in keys:
#         try:
#             if not flat_data[k]:
#                 click.echo(f"{k} mandatory")
#                 sys.exit(1)
#             if k == "kind" and flat_data[k] not in [
#                 "Organization",
#                 "Dataset",
#                 "Solution",
#                 "Connector",
#                 "Workspace",
#             ]:
#                 click.echo(f"{k} : {flat_data[k]} not accepted")
#                 return False
#             return True
#         except Exception:
#             sys.exit(1)

# def run(dir: str):
#     observer = Observer()
#     event_handler = Handler()
#     observer.schedule(event_handler, dir, recursive=True)
#     observer.start()
#     observer.join()

# class Handler(FileSystemEventHandler):

#     @staticmethod
#     def on_any_event(event):
#         if event.is_directory:
#             return None

#         elif event.event_type == 'created':
#             # Take any action here when a file is first created.
#             click.echo("created")
#         elif event.event_type == 'modified':
#             # Taken any action here when a file is modified.
#             click.echo(f"modified {event}")

# def detekt(kind: str, path: pathlib.Path) -> bool:
#     g = glob.glob(path)
#     g = g[0] if len(g) else None
#     if g is None:
#         return False
#     click.echo(g)
#     d = os.stat(g).st_mtime
#     s = pathlib.Path("./test.yaml")
#     if s.exists():
#         mstate = yaml.load(s.open("r"), Loader=yaml.SafeLoader)
#         project_state = mstate
#         if kind in mstate and mstate[kind] != d:
#             return True
#     else:
#         project_state = dict()
#     project_state[kind] = d
#     data = yaml.dump(project_state)
#     s.write_text(data)
#     return False


@command(name="apply")
@argument("folder_deploy", type=click.Path(exists=True, dir_okay=True))
def capply(folder_deploy: Path, ):
    """
    Apply a deployment
    """
    # env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])
    files_to_deploy = []
    files_ = pathlib.Path(folder_deploy).iterdir()
    for f in files_:
        if not f.is_dir() and f.suffix in [".yaml", "yml"]:
            files_to_deploy.append(f.absolute())
        else:
            for j in f.iterdir():
                if not j.is_dir() and j.suffix in [".yaml", "yml"]:
                    files_to_deploy.append(j)
    iter_deploy(files_to_deploy, len(files_to_deploy))


def iter_deploy(files: list, repeat: int):
    if len(files) == 0 or repeat == 0:
        click.echo(click.style('Completed!', fg='bright_yellow'))
        sys.exit(0)
    else:
        file_ = pathlib.Path(files[-1])
        data = file_.open().read()
        deploy = env.fill_specification(data)
        # go = check(deploy_dict, ["kind", "state.context", "state.platform"])
        kind = deploy.get("kind")
        # context = deploy.get("state").get("context")
        # platform = deploy.get("state").get("platform")
        # state = populate_state(context_id=context, platform_id=platform)
        # spec = deploy.get("spec")
        # dependencies = deploy.get("spec").get("dependencies")
        click.echo(click.style(kind, fg="green"))
        # print(state)
        # print(context)
        # print(platform)
        # print(spec)
        # print(dependencies)
        # match kind:
        #     case "Organization":
        #         deploy_organization(
        #             azure_token="",
        #             state=state,
        #             spec=spec,
        #             dependencies=dependencies,
        #             filename=files[-1],
        #         )
        #     case "Dataset":
        #         if deploy_dataset(spec=spec, config=config, filename=files[-1]):
        #             files.pop()
        #         else:
        #             t = files.pop()
        #             files.insert(0, t)
        #             repeat = repeat - 1
        #     case "Solution":
        #         if not go:
        #             files.pop()
        #             iter_deploy(files, repeat - 1)
        #         if deploy_solution(spec=spec, config=config, filename=files[-1]):
        #             files.pop()
        #         else:
        #             t = files.pop()
        #             files.insert(0, t)
        #             repeat = repeat - 1
        #     case "Connector":
        #         if not go:
        #             files.pop()
        #             iter_deploy(files, repeat - 1)
        #         type_ = deploy["type"]
        #         if deploy_connector(
        #             spec=spec, type=type_, config=config, filename=files[-1]
        #         ):
        #             files.pop()
        #         else:
        #             t = files.pop()
        #             files.insert(0, t)
        #             repeat = repeat - 1
        #     case "Workspace":
        #         if not go:
        #             files.pop()
        #             iter_deploy(files, repeat - 1)
        #         if deploy_workspace(spec=spec, config=config, filename=files[-1]):
        #             files.pop()
        #         else:
        #             t = files.pop()
        #             files.insert(0, t)
        #             repeat = repeat - 1
        files.pop()
        repeat = repeat - 1
        iter_deploy(files, repeat)


def populate_state(context_id: str, platform_id: str):
    state = env.get_state_from_local(context_id, platform_id)
    return state


def deploy_organization(azure_token: str, state: dict, spec: dict, deps: dict, filename: str) -> bool:
    click.echo("organization deployment")
    id = spec.get("payload").get("id")
    print(id)
    # organization_service = OrganizationService(azure_token=azure_token, spec=spec, state=state)
    # if not id:
    #     response = organization_service.create()
    #     organization = response.json()
    #     state["services"]["api"]["organization_id"] = organization.get("id")
    #     env.store_state_in_local(state)
    #     env.store_state_in_cloud(state)
    # else:
    #     response = organization_service.update()
    #     response_json = response.json()
    #     old_security = response_json.get("security")
    #     security_spec = organization_service.update_security(old_security=old_security)
    #     response_json["security"] = security_spec
    #     organization = response_json
    # click.echo(message="Organization deployed")


# def deploy_solution(
#     azure_token: str, state: dict, spec: dict, filename: pathlib.Path
# ) -> bool:
#     click.echo("deploy solution")
#     api = SolutionService(azure_token=azure_token, state=state, spec=spec)
#     sol_id = state["state"]["api"]["solution_id"]
#     spec["id"] = sol_id
#     runTemplates: dict = spec["sidecars"]["run_template"]
#     for run_item in runTemplates:
#         id = run_item["id"]
#         handlers = run_item["handlers"]
#         for h, deploy in handlers.items():
#             parent = filename.parent
#             run_id_to_check = parent / f"run_templates/{id}/{h}"
#             if not run_id_to_check.exists():
#                 pass
#             package_run_template(
#                 id=id, handler_id=h, deploy=deploy, entry=filename, config=state
#             )
#     payload = spec["payload"]
#     payload["id"] = sol_id
#     data = api.update(payload).data if sol_id else api.create(payload).data
#     state["state"]["api"]["solution_id"] = data["id"]
#     api.security(payload)
#     api.store(state)
#     click.echo(message=f"Deployment solution {sol_id}")
#     return data["id"] != ""

# def deploy_connector(
#     spec: dict, type: str, config: dict, filename: pathlib.Path
# ) -> bool:
#     return True
#     click.echo("deploy connector")
#     cfig = populate(config)
#     api = ApiConnectorService(cfig)
#     connector_id = cfig["state"]["api"]["connector"][f"{type}_id"]
#     spec = spec["payload"]
#     data = api.update(spec).data if connector_id else api.create(spec).data
#     cfig["state"]["api"]["connector"][f"{type}_id"] = data["id"]
#     api.store(cfig)
#     click.echo(message=f"Deployment connector {connector_id}")

# def deploy_workspace(spec: dict, config: dict, filename: pathlib.Path) -> bool:
#     return True
#     click.echo("deploy workspace")
#     cfig = populate(config)
#     api = ApiWorkspaceService(cfig)
#     work_id = cfig["state"]["api"]["workspace"]
#     spec = spec["payload"]
#     data = api.update(spec).data if work_id else api.create(spec).data
#     cfig["state"]["api"]["workspace_id"] = data["id"]
#     api.store(cfig)
#     click.echo(message=f"Deployment workspace {work_id}")

# def deploy_dataset(spec: dict, config: dict, filename: pathlib.Path) -> bool:
#     return True
#     click.echo("deploy dataset")
#     cfig = populate(config)
#     state_id = cfig["state"].get("id")
#     bundle_dataset_and_store(
#         state_id=state_id,
#         name="test",
#         project="testproject",
#         filename=filename,
#         config=cfig,
#     )

# def package_run_template(
#     id: str, handler_id: str, deploy: bool, entry: pathlib.Path, config: dict
# ) -> bool:
#     if handler_id not in ["postrun", "prerun", "parameters_handler"]:
#         click.echo(f"{id} parameter id not found")
#         return False
#     new_entry = entry.parent / "run_templates" / id / handler_id
#     if not new_entry.exists():
#         click.echo(new_entry, "not found")
#         return False
#     t = shutil.make_archive(
#         f"{entry.parent}/run_templates/{id}/{handler_id}/{handler_id}", "zip", new_entry
#     )
#     org_id = config["state"]["api"].get("organization_id")
#     sol_id = config["state"]["api"].get("solution_id")
#     check = blob_client(config).get_container_client(container=org_id)
#     if not check.exists():
#         logger.info(f"Container '{org_id}' not found")
#         return CommandResponse.fail()
#     client = blob_client(config).get_blob_client(
#         container=org_id, blob=f"{sol_id}/{id}/{handler_id}.zip"
#     )
#     if client.exists():
#         client.delete_blob()
#     with open(t, "rb") as data:
#         client.upload_blob(data)
#         # click.echo(f"Successfully upload run template {sol_id}/{id}/{handler_id}")
#     os.remove(t)
#     return True

# def bundle_retrieve(name: str):
#     home = pathlib.Path().home()
#     os.system(f"git clone {name}.bundle {home}/.config/babylon")
#     shutil.rmtree(f"{home}/.config/babylon/.git")
#     shutil.copytree(f"{home}/.config/babylon", pathlib.Path().cwd(), dirs_exist_ok=True)
#     shutil.rmtree(f"{home}/.config/babylon/")
#     os.mkdir(f"{home}/.config/babylon")
#     os.remove(f"{name}.bundle")

# def bundle_dataset_and_store(
#     state_id: str, name: str, project: str, filename: pathlib.Path, config: dict
# ):
#     home = pathlib.Path().home()
#     entry = filename.parent / "data"
#     shutil.copytree(src=entry, dst=home / ".config/babylon/data", dirs_exist_ok=True)
#     os.chdir(home / ".config/babylon/data")
#     os.system("git init -q")
#     os.system("git add . -v")
#     os.system("git commit -m 'project commit'")
#     os.system(f"git bundle create {name}.bundle --all")
#     shutil.rmtree(".git")
#     data = pathlib.Path(f"{name}.bundle").open("rb")
#     guidd = state_id or uuid4()
#     check = blob_client(config).get_container_client(container="babylon-projects")
#     if not check.exists():
#         blob_client(config).create_container(name="babylon-projects")
#     bundle = blob_client(config).get_blob_client(
#         container="babylon-projects", blob=f"{project}/{str(guidd)}.{name}.bundle"
#     )
#     if bundle.exists():
#         bundle.delete_blob()
#     bundle.upload_blob(data)
#     logger.info(f"Saved with id: {project}/{str(guidd)}.{name}.bundle")
#     # os.remove(f"{name}.bundle")

import os
import argparse
import sys
import yaml
import uuid

from glob import glob
from pathlib import Path

parser = argparse.ArgumentParser(description="get context")
parser.add_argument("config_path", type=str)
parser.add_argument("context", type=str)
parser.add_argument("platform", type=str)

rsc = [
    "api",
    "app",
    "azure",
    "babylon",
    "github",
    "platform",
    "powerbi",
    "webapp",
]


def get_config_files(cnf: Path, ctx: str, plt: str):
    """Retrieve all configuration files"""
    checking = []
    existing_files_platform = list(map(lambda x: glob(str(cnf / f"*.{plt}.{x}.yaml")), rsc))
    for item in existing_files_platform:
        checking += item
    if not checking:
        print(f"ERROR: platform={plt}")
        print(f"{plt} platform doesn't match with your configuration files")
        sys.exit(1)
    response = []
    _list = list(map(lambda x: glob(str(cnf / f"{ctx}.{plt}.{x}.yaml")), rsc))
    if not _list:
        print(f"ERROR: context={ctx}, platform={plt}")
        print(f"{ctx} context not match with your configuration files")
        sys.exit(1)
    for item in _list:
        item = item[0] if len(_list) else ""
        if not Path(item).exists():
            print(f"{item} not found")
            sys.exit(1)
        response += [item]
    return response


def migrate(ctx: str, plt: str, config_path: str) -> list[Path]:
    config_dir = Path(config_path).absolute()
    state = dict()
    result = get_config_files(cnf=config_dir, ctx=ctx, plt=plt)
    response = dict()
    for item in result:
        service = os.path.basename(Path(item)).split(".")[2]
        data = yaml.load(Path(item).open("r"), Loader=yaml.SafeLoader)
        data = data[args.context]
        response[service] = data
    state["id"] = str(uuid.uuid4())
    state["context"] = ctx
    state["platform"] = plt
    state["services"] = response
    state_dir = Path().home() / ".config/cosmotech/babylon"
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
    s = state_dir / f"state.{ctx}.{plt}.yaml"
    s.write_bytes(yaml.dump(data=state, indent=2).encode("utf-8"))


def checking_migration(ctx: str, plt: str) -> bool:
    babydir = ".config/cosmotech/babylon"
    s = Path(Path().home() / babydir / f"state.{ctx}.{plt}.yaml")
    return s.exists()


def check_config_directory(config_path: str):
    config_dir = Path(config_path).absolute()
    if not config_dir.exists():
        print(f"""
We are sorry, we can't process your request.
Babylon configuration files {config_dir} not found""")
        print(Path().absolute())
        sys.exit(1)


if __name__ == "__main__":
    args = parser.parse_args()
    check_config_directory(args.config_path)
    migrate(ctx=args.context, plt=args.platform, config_path=args.config_path)
    result = checking_migration(ctx=args.context, plt=args.platform)
    if result:
        print("migration completed")

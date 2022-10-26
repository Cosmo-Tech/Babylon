import logging
import pathlib
from typing import Optional

import click
from click import command
from git import Repo
from git.exc import GitCommandError

from Babylon.main import main

logger = logging.getLogger("Babylon")


def command_tree(obj):
    if isinstance(obj, click.Group):
        return {name: command_tree(value) for name, value in obj.commands.items()}


def file_deps(tree, _path):
    _name = _path + '/__init__.py'
    if not pathlib.Path(_name).exists():
        return
    n_tree = dict(name=_path + '/__init__.py')
    for k, v in tree.items():
        if v:
            _p = _path + "/groups/" + k.replace('-', '_')
            n_tree.setdefault('groups', [])
            content = file_deps(v, _p)
            if content:
                n_tree['groups'].append(content)
        else:
            _p = _path + "/commands/" + k.replace('-', '_') + '.py'
            n_tree.setdefault('cmds', [])
            n_tree['cmds'].append(_p)
    return n_tree


def flatten_tree(deps_tree):
    r = dict()
    deps = set(deps_tree.get('cmds', [])[:])
    groups = deps_tree.get('groups', {})
    name = deps_tree.get('name', '')
    r[name] = deps
    for cmd in deps_tree.get('cmds', []):
        r[cmd] = {cmd}
    for group in groups:
        _r, _deps = flatten_tree(group)
        r = {**r, **_r}
        r[name].update(_deps)
    return r, deps


def path_to_cmd(_path):
    return _path[:-3].replace("/groups/", " ").replace("/commands/", " ").replace("_", "-").lower()


def augment_with_utils(deps_tree):
    new_tree = {**deps_tree}
    for k, v in deps_tree.items():
        _f_utils = set()
        if pathlib.Path(k).exists():
            with open(k, 'r') as _f:
                for line in _f:
                    if ".utils" in line:
                        try:
                            _f_utils.add(line.split("import")[0].split("utils.")[1].strip())
                        except IndexError:
                            _f_utils.add("__init__")
        for _util in list(_f_utils):
            util_path = f"Babylon/utils/{_util}.py"
            new_tree.setdefault(util_path, set())
            new_tree[util_path].update(v)
    return new_tree


@command()
@click.argument("git_ref")
@click.option("-o", "--output", "output", help="Target file to write list of commands to be tested")
def tests_todo(git_ref: str, output: Optional[str]):
    """List commands that require testing since GIT_REF"""
    r = Repo(".")

    h = r.head.commit

    try:
        diffs = h.diff(git_ref)
    except GitCommandError:
        logger.error(f"{git_ref} is not a valid git reference.")
        return

    tree = file_deps(command_tree(main), 'Babylon')

    tree['name'] = "Babylon/main.py"

    tree2 = flatten_tree(tree)[0]

    tree3 = augment_with_utils(tree2)

    path_to_check = set()

    diffs_paths = list(d.a_path for d in diffs)

    for diff in diffs_paths:
        path_to_check.update(tree3.get(diff, []))

    if path_to_check:
        logger.info("Commands that require a test :")
        if output:
            with open(output, "w") as f:
                f.write("")

        for cmd in list(sorted(map(path_to_cmd, list(path_to_check)))):
            logger.info(f"  {cmd}")
            if output:
                with open(output, "a") as f:
                    f.write(f"{cmd}\n")
    else:
        logger.info("No command requires a test")

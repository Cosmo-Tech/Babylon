import jmespath
import yaml
import click
import logging
import pathlib

from typing import Any
from click import Path, argument, command, option
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from flatten_json import flatten, unflatten_list
from ruamel.yaml import YAML

from Babylon.utils.update_section import get_section_and_replace

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@option("--flatten", "flat", is_flag=True, help="Flatten option")
@option("--dashboard_view", "dashboard_view", is_flag=True, help="dashboard_view section")
@option("--scenario_view", "scenario_view", is_flag=True, help="scenario_view section")
@option("--origin", "origin_file", required=True, type=Path(path_type=pathlib.Path), help="yaml file to change")
@option("--target", "target_file", required=True, type=Path(path_type=pathlib.Path), help="yaml file to dump changes")
@option("--query", "query", type=str, help="Jmespath query")
@option("--section", "section", type=str, help="section in yaml file to perform changes")
@argument("stream")
def upsert(origin_file: pathlib.Path, target_file: pathlib.Path, query: str, section: str, flat: bool, stream: Any,
           dashboard_view: bool, scenario_view: bool) -> CommandResponse:
    """
    Insert or update an object into section of yaml file
    """
    yaml_loader = YAML()
    data_o = yaml.safe_load(origin_file.open())
    data_o_f = flatten(yaml.safe_load(origin_file.open()), separator=".")
    data_s = click.get_text_stream('stdin', encoding="utf-8")
    data_stdin = yaml.safe_load(data_s.read())
    result = None
    if query and not flat and (dashboard_view or scenario_view):
        _match = jmespath.search(query, data_o)
        if _match is None:
            logger.info("Query error: object not found")
            return CommandResponse.fail()
        key = _match.get("key")
        old = _match.get("value")
        try:
            _key = "dashboardsView" if dashboard_view else "scenarioview"
            idx = data_o["webApp"]["options"]["charts"][_key].index(old)
        except AttributeError as exp:
            logger.warn(exp)
            return CommandResponse.fail()

        if _match:
            result = data_o
            for item in data_stdin:
                if item['reportId'] != old['reportId']:
                    continue
                d = dict()
                d[key] = [item]
                test = flatten(d, separator=".")
                for k, v in test.items():
                    i = k.index("0")
                    end = k[i + 2:]
                    nk = f"{key}.{idx}.{end}"
                    data_o_f.update({nk: v})
                result = unflatten_list(data_o_f, separator=".")

    if query and not flat and not (dashboard_view or scenario_view):
        _match = jmespath.search(query, data_o)
        if _match is None:
            logger.info("Query error: object not found")
            return CommandResponse.fail()
        key = _match.get("key")
        old = _match.get("value")
        try:
            idx = data_o[key].index(old)
        except AttributeError as exp:
            logger.warn(exp)
            return CommandResponse.fail()

        if _match:
            result = data_o
            for item in data_stdin:
                if item['id'] != old['id']:
                    continue
                d = dict()
                d[key] = [item]
                test = flatten(d, separator=".")
                for k, v in test.items():
                    i = k.index("0")
                    end = k[i + 2:]
                    nk = f"{key}.{idx}.{end}"
                    data_o_f.update({nk: v})
                result = unflatten_list(data_o_f, separator=".")

    if not query and not flat and not (dashboard_view or scenario_view):
        for item in enumerate(data_stdin):
            _q = f"{section}[?id=='{item['id']}'] |"
            _q += "{" + "\"key\": '{s}'".format(s=section) + ", value: [0]}"
            _match = jmespath.search(_q, data_o)
            key = _match.get("key") if _match else section
            found = _match.get("value") if _match else False
            if found:
                idx = data_o[key].index(_match.get("value"))
                d = dict()
                d[key] = [item]
                test = flatten(d, separator=".")
                for k, v in test.items():
                    i = k.index("0")
                    end = k[i + 2:]
                    nk = f"{key}.{idx}.{end}"
                    data_o_f.update({nk: v})
                result = unflatten_list(data_o_f, separator=".")
            else:
                data_o[key] = data_o[key] or []
                data_o[key].append(item)
                result = data_o

    if not query and flat:
        for item in data_stdin:
            result = get_section_and_replace(section, item, data_o)
    with target_file.open(mode='w') as _f:
        yaml_loader.dump(result, target_file)
        logger.info(f"Content dumped in {_f.name}")
    return CommandResponse.success()

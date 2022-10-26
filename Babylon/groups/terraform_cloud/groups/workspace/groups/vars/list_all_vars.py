import logging

from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

logger = logging.getLogger("Babylon")


def list_all_vars(api: TFC, workspace_id: str, lookup_var_sets: bool = True) -> list[dict]:
    """
    List all existing vars from a workspace
    either in a setted var or in a variable set
    :param api: the API object for terraform
    :param workspace_id: the id of the workspace to read
    :param lookup_var_sets: should the variables sets of the workspace be listed in the results ?
    :return: the list of all the var data
    """

    try:
        ws = api.workspaces.show(workspace_id=workspace_id)
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return []
    workspace_name = ws['data']['attributes']['name']
    ws_vars = api.vars.list(workspace_name=workspace_name)
    r = []

    existing_keys = []

    def get_attr_key(_r):
        return _r.get('attributes', {}).get('key', '')

    for ws_var in sorted(ws_vars.get('data'), key=get_attr_key):
        r.append(ws_var)
        existing_keys.append(ws_var['attributes']['key'])

    if lookup_var_sets:
        var_sets = api.var_sets.list_for_workspace(workspace_id)

        for _var_set in var_sets['data']:
            for vs_var in api.var_sets.list_vars_in_varset(_var_set['id'])['data']:
                _k = vs_var['attributes']['key']
                if _k not in existing_keys:
                    r.append(vs_var)

    return r

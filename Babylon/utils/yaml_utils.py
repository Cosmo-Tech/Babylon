import json
import yaml

def yaml_to_json(yaml_str: str) -> str:
    """
    Converts a yaml string to a json string
    """
    data = yaml.safe_load(yaml_str)
    return json.dumps(data, indent=4, default=str, ensure_ascii=True)

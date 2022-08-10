import re


def is_valid_command_name(string: str) -> bool:
    """
    Check if a given string is a valid command name
    :param string: the string to check
    :return: True if the string is a valid command name
    """
    pattern = r'^[a-zA-Z]\w*$'
    return bool(re.search(pattern, string))

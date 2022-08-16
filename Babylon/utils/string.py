import re


def is_valid_command_name(string: str) -> bool:
    """
    Check if a given string is a valid command name
    :param string: the string to check
    :return: True if the string is a valid command name
    """
    pattern = r'^[a-zA-Z]\w*$'
    return bool(re.search(pattern, string))


MAX_LINE_LENGTH = 120


def to_header_line(string: str) -> str:
    if (length := len(string)) > MAX_LINE_LENGTH:
        return string
    elif length == 0:
        return "-" * MAX_LINE_LENGTH
    else:
        missing = MAX_LINE_LENGTH - length - 2
        return f"{'-' * (missing // 2)} {string} {'-' * (missing // 2)}"

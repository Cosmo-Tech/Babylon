import re

MAX_LINE_LENGTH = 120


def is_valid_command_name(string: str) -> bool:
    """
    Check if a given string is a valid command name
    :param string: the string to check
    :return: True if the string is a valid command name
    """
    pattern = r'^[a-zA-Z]\w*$'
    return bool(re.search(pattern, string))


def to_header_line(string: str) -> str:
    """
    Convert a string to a header line of maximum length of MAX_LINE_LENGTH

    will center the string between `-` to show a delimitation
    :param string: the string to transform
    :return: the string centered with `-` padding
    """
    if (length := len(string)) > MAX_LINE_LENGTH:
        return string
    if length == 0:
        return "-" * MAX_LINE_LENGTH
    missing = MAX_LINE_LENGTH - length - 2
    return f"{'-' * (missing // 2)} {string} {'-' * (missing // 2)}"

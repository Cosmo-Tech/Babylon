import re


def is_valid_name(string):
    pattern = r'^[a-zA-Z]\w*$'
    return re.search(pattern, string)

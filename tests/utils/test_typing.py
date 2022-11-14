import random
import string

from Babylon.utils.typing import DEPLOY_STRING
from Babylon.utils.typing import PATH_SYMBOL
from Babylon.utils.typing import PLATFORM_STRING
from Babylon.utils.typing import QueryType
from Babylon.utils.typing import WORKING_DIR_STRING


def gen_random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def test_extract_deploy():
    random_text = gen_random_string(10)
    composed_string = f"{PATH_SYMBOL}{DEPLOY_STRING}{PATH_SYMBOL}{random_text}"
    _type, _path, _query = QueryType.extract_value_content(composed_string)
    assert _type == DEPLOY_STRING
    assert _path is None
    assert _query == random_text


def test_extract_platform():
    random_text = gen_random_string(10)
    composed_string = f"{PATH_SYMBOL}{PLATFORM_STRING}{PATH_SYMBOL}{random_text}"
    _type, _path, _query = QueryType.extract_value_content(composed_string)
    assert _type == PLATFORM_STRING
    assert _path is None
    assert _query == random_text


def test_extract_working_dir():
    random_text = gen_random_string(10)
    random_text2 = gen_random_string(10)
    composed_string = f"{PATH_SYMBOL}{WORKING_DIR_STRING}[{random_text2}]{PATH_SYMBOL}{random_text}"
    _type, _path, _query = QueryType.extract_value_content(composed_string)
    assert _type == WORKING_DIR_STRING
    assert _path == random_text2
    assert _query == random_text


def test_extract_non_string():
    assert QueryType.extract_value_content({'this is not a string'}) is None


def test_extract_working_dir_wo_path():
    random_text = gen_random_string(10)
    assert QueryType.extract_value_content(f"{PATH_SYMBOL}{WORKING_DIR_STRING}[]{PATH_SYMBOL}{random_text}") is None


def test_extract_working_dir_wo_query():
    random_text = gen_random_string(10)
    assert QueryType.extract_value_content(f"{PATH_SYMBOL}{WORKING_DIR_STRING}[{random_text}]{PATH_SYMBOL}") is None


def test_extract_deploy_wo_query():
    assert QueryType.extract_value_content(f"{PATH_SYMBOL}{DEPLOY_STRING}{PATH_SYMBOL}") is None


def test_extract_platform_wo_query():
    assert QueryType.extract_value_content(f"{PATH_SYMBOL}{PLATFORM_STRING}{PATH_SYMBOL}") is None

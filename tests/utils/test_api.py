import logging
from unittest.mock import patch, mock_open
from Babylon.utils import api


def test_camel_underscore_ok():
    """Camel Underscore test"""
    assert api.camel_to_underscore("cAmelCase") == "c_amel_case"


def test_camel_undescore_empty():
    """Camel underscore test"""
    assert api.camel_to_underscore("") == ""


def test_camel_undescore_one():
    """Camel underscore test"""
    assert api.underscore_to_camel("one") == "one"


def test_underscore_camel_ok():
    """Camel Underscore test"""
    assert api.underscore_to_camel("c_amel_case") == "cAmelCase"


def test_underscore_camel_empty():
    """Camel underscore test"""
    assert api.underscore_to_camel("") == ""


def test_underscore_camel_one():
    """Camel underscore test"""
    assert api.underscore_to_camel("one") == "one"


def test_convert_keys_case_ok_1():
    """Convert keys case test"""
    converted = api.convert_keys_case({"a": 1, "b": 2}, lambda x: x.upper())
    assert list(converted.keys()) == ["A", "B"]


def test_convert_keys_case_ok_2():
    """Convert keys case test"""
    converted = api.convert_keys_case([{"a": 1}, {"b": 1}], lambda x: x.upper())
    assert converted == [{"A": 1}, {"B": 1}]


def test_convert_keys_case_ok_3():
    """Convert keys case test"""
    params = {"parametersValues": {"a": 1, "b": 1}}
    # Should ignore key case if inside a parametersValues
    converted = api.convert_keys_case(params, lambda x: x.upper())
    assert converted["parametersValues".upper()] == params["parametersValues"]


def test_get_api_file_missing_1():
    """Get Api File test"""
    file = api.get_api_file("myfile", False, logging.getLogger("test"))
    assert not file


def test_get_api_file_yaml():
    """Get Api File test"""
    with patch("builtins.open", mock_open(read_data="test: 10\n")), patch("pathlib.Path.exists", lambda x: True):
        data = api.get_api_file("test.yaml", False, logging)
        assert data == {"test": 10}


def test_get_api_file_json():
    """Get Api File test"""
    with patch("builtins.open", mock_open(read_data="{\"test\": 10}")), patch("pathlib.Path.exists", lambda x: True):
        data = api.get_api_file("test.json", False, logging)
        assert data == {"test": 10}

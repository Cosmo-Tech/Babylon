from pathlib import Path
from unittest.mock import patch, mock_open
from Babylon.utils.yaml_utils import read_yaml_key, compare_yaml_keys, complete_yaml, set_nested_key


def multi_mock_open(*file_contents):
    """Create a mock "open" that will mock open multiple files in sequence
    Args:
        *file_contents ([str]): a list of file contents to be returned by open
    Returns:
        (MagicMock) a mock opener that will return the contents of the first
            file when opened the first time, the second file when opened the
            second time, etc.
    """
    mock_files = [mock_open(read_data=content).return_value for content in file_contents]
    mock_opener = mock_open()
    mock_opener.side_effect = mock_files
    return mock_opener


def test_read_yaml_fail():
    """Testing yaml utils"""
    assert not read_yaml_key(Path("tests"), "plop")


def test_read_yaml_fail_2():
    """Testing yaml utils"""
    file = Path("tests/resources/plugin_0/plugin_config.yaml")
    assert not read_yaml_key(file, "plop")


def test_read_yaml_ok():
    """Testing yaml utils"""
    file = Path("tests/resources/plugin_0/plugin_config.yaml")
    assert read_yaml_key(file, "plugin_name")


def test_compare_yaml_ok():
    """Testing yaml utils"""
    with patch("pathlib.Path.open", mock_open(read_data="a: 1\nb: 3\n")):
        response = compare_yaml_keys(Path("test1"), Path("test2"))
        assert {"a", "b"} == set(response[0])
        assert not response[1]


def test_compare_yaml_fail():
    """Testing yaml utils"""
    with patch("pathlib.Path.open", multi_mock_open("a: 1\n", "b: 1\n")):
        response = compare_yaml_keys(Path("test1"), Path("test2"))
        assert {"a"} == set(response[0])
        assert {"b"} == set(response[1])


def test_complete_yaml():
    """Testing yaml utils"""
    with patch("pathlib.Path.open", multi_mock_open("a: 1\n", "b: 1\n", "")), patch("yaml.safe_dump") as file:
        complete_yaml(Path("test1"), Path("test2"))
        file.assert_called()
        args, _ = file.call_args_list[0]
        assert args[0] == {"a": 1, "b": 1}


def test_set_nested():
    """Testing yaml utils"""
    assert set_nested_key({}, ["hey", "you"], "there") == {"hey": {"you": "there"}}

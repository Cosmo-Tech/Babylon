import logging
import pathlib
from unittest.mock import patch, mock_open
from Babylon.utils.configuration import Configuration

@patch("pathlib.Path.exists")
def test_init_exists(exists: object):
    """Testing configuration"""
    exists.return_value = True
    Configuration(logging, pathlib.Path("tests"))

@patch("shutil.copytree")
def test_init_create(copytree: object):
    """Testing configuration"""
    _ = copytree
    with patch("builtins.open", mock_open()) as mock_file:
        Configuration(logging, pathlib.Path("pleaseDoNotExistOrIWillFail"))
    mock_file.assert_called()
    mock_file.return_value.write.assert_called()

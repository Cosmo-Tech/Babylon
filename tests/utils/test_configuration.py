import logging
from pathlib import Path
from unittest.mock import patch, mock_open
from Babylon.utils.configuration import Configuration


@patch("pathlib.Path.exists")
def test_init_exists(exists: object):
    """Testing configuration"""
    exists.return_value = True
    Configuration(Path("tests"))


@patch("shutil.copytree")
def test_init_create(copytree: object):
    """Testing configuration"""
    _ = copytree
    with patch("builtins.open", mock_open()) as mock_file:
        Configuration(Path("pleaseDoNotExistOrIWillFail"))
    mock_file.assert_called()
    mock_file.return_value.write.assert_called()


def test_config_add_plugin():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    plugin = config.add_plugin(Path("tests/resources/plugin_0"))
    assert plugin == "plugin_0"


def test_config_add_plugin_missing():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert not config.add_plugin(Path("tests/resources/DoesNotExists"))


def test_config_add_plugin_broken():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert not config.add_plugin(Path("tests/resources/plugin_broken"))


def test_config_add_plugin_broken_2():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert not config.add_plugin(Path("tests/resources/plugin_broken_2"))


def test_config_add_plugin_duplicate():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    config.add_plugin(Path("tests/resources/plugin_0"))
    assert not config.add_plugin(Path("tests/resources/plugin_0"))


def test_config_plugins_available():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    config.add_plugin(Path("tests/resources/plugin_0"))
    plugins = ",".join(plugin for plugin in config.get_available_plugin())
    assert "plugin_0" in plugins


def test_config_plugins_active():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    config.add_plugin(Path("tests/resources/plugin_0"))
    plugins = ",".join(plugin[0] for plugin in config.get_active_plugins())
    assert "plugin_0" in plugins


def test_config_plugins_deactivate():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    config.add_plugin(Path("tests/resources/plugin_0"))
    config.deactivate_plugin("plugin_0")
    plugins = ",".join(plugin[0] for plugin in config.get_active_plugins())
    assert "plugin_0" not in plugins


def test_config_plugins_deactivate_fail():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    response = config.deactivate_plugin("plugin_0")
    assert not response


def test_config_plugins_remove():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    config.add_plugin(Path("tests/resources/plugin_0"))
    config.add_plugin(Path("tests/resources/plugin_1"))
    config.remove_plugin("plugin_0")
    plugins = ",".join(plugin for plugin in config.get_available_plugin())
    assert "plugin_0" not in plugins


def test_config_plugins_activate():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    config.add_plugin(Path("tests/resources/plugin_0"))
    config.deactivate_plugin("plugin_0")
    config.activate_plugin("plugin_0")
    plugins = ",".join(plugin[0] for plugin in config.get_active_plugins())
    assert "plugin_0" in plugins


def test_config_plugins_activate_fail():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    response = config.activate_plugin("thisIsNotAvailable")
    assert not response


def test_list_deploys():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert any("deploy.yaml" in str(path) for path in config.list_deploys())


def test_list_platforms():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert any("platform.yaml" in str(path) for path in config.list_platforms())


def test_set_deploy_fail():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert not config.set_deploy(Path("thisDoesNotExist"))


def test_set_deploy_ok():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert config.set_deploy(Path("tests/environments/Default/deployments/deploy.yaml"))


def test_set_platform_fail():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert not config.set_platform(Path("thisDoesNotExist"))


def test_set_platform_ok():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert config.set_platform(Path("tests/environments/Default/platforms/platform.yaml"))


def test_save_config():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    with patch("builtins.open", mock_open()) as mock_file:
        config.save_config()
    mock_file.assert_called()
    mock_file.return_value.write.assert_called()


def test_check_api_ok():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert config.check_api()

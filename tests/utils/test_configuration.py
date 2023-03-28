import os
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
        c = Configuration(Path("pleaseDoNotExistOrIWillFail"))
        c.initialize()
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


def test_set_deploy_fail():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert not config.set_deploy(Path("thisDoesNotExist"))


def test_set_deploy_ok():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert config.set_deploy(Path("tests/environments/Default/deploy.yaml"))


def test_set_platform_fail():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert not config.set_platform(Path("thisDoesNotExist"))


def test_set_platform_ok():
    """Testing configuration"""
    config = Configuration(Path("tests/environments/Default"))
    assert config.set_platform(Path("tests/environments/Default/platform.yaml"))


@patch('click.edit')
def test_create_deploy_ok(click_edit):
    """Test creating deployement file"""
    config = Configuration(Path("tests/environments/Default"))
    config.create_deploy('test')

    click_edit.assert_called_once()
    test_file_path = config.config_dir.joinpath('test.yaml')
    assert test_file_path.exists()
    os.remove(test_file_path)


@patch('click.edit')
def test_create_deploy_exist(click_edit):
    """Test creating on existing deployement file"""
    config = Configuration(Path("tests/environments/Default"))
    config.create_deploy('deploy')

    click_edit.assert_not_called()
    test_file_path = config.config_dir.joinpath('deploy.yaml')
    assert test_file_path.exists()


@patch('click.edit')
def test_create_platform_ok(click_edit):
    """Test creating platform file"""
    config = Configuration(Path("tests/environments/Default"))
    config.create_platform('test')

    click_edit.assert_called_once()
    test_file_path = config.config_dir.joinpath('test.yaml')
    assert test_file_path.exists()
    os.remove(test_file_path)


@patch('click.edit')
def test_create_platform_exist(click_edit):
    """Test creating on existing platform file"""
    config = Configuration(Path("tests/environments/Default"))
    config.create_platform('platform')

    click_edit.assert_not_called()
    test_file_path = config.config_dir.joinpath('platform.yaml')
    assert test_file_path.exists()


@patch('click.edit')
def test_edit_deploy_ok(click_edit):
    """Test edit deployment file"""
    config = Configuration(Path("tests/environments/Default"))
    # config.edit_deploy('deploy.yaml') should work like this of config.edit_deploy()
    config.edit_deploy(config.config_dir.joinpath(config.deploy))
    click_edit.assert_called_once()


@patch('click.edit')
def test_edit_deploy_not_exist(click_edit):
    """Test edit no existing deployment file"""
    config = Configuration(Path("tests/environments/Default"))
    # config.edit_deploy('deploy.yaml') should work like this of config.edit_deploy()
    config.edit_deploy(Path('not_existing'))
    click_edit.assert_not_called()


@patch('click.edit')
def test_edit_platform_ok(click_edit):
    """Test edit iplatform file"""
    config = Configuration(Path("tests/environments/Default"))
    config.edit_platform(config.config_dir.joinpath(config.platform))
    click_edit.assert_called_once()


@patch('click.edit')
def test_edit_platform_not_exist(click_edit):
    """Test edit no existing platform file"""
    config = Configuration(Path("tests/environments/Default"))
    config.edit_platform(Path('not_existing'))
    click_edit.assert_not_called()


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


def test_to_string():
    """Testing __str__ function"""
    config = Configuration(Path("tests/environments/Default"))
    config.__str__()

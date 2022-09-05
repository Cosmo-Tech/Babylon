import os
import pathlib

from click.testing import CliRunner

TEST_FOLDER = list(pathlib.Path(__file__).parents)[0]
os.environ['BABYLON_CONFIG_DIRECTORY'] = str(TEST_FOLDER / 'environments' / 'Default')
os.environ['BABYLON_RUNNING_TEST'] = 'True'


def test_config_display(capsys):
    from Babylon.main import main
    runner = CliRunner()
    _ = runner.invoke(main, '--tests config display')
    captured = capsys.readouterr()
    assert "dir: " + os.environ['BABYLON_CONFIG_DIRECTORY'] in captured.out

import logging
from pathlib import Path
from unittest.mock import patch

from Babylon.utils.working_dir import WorkingDir


def test_working_init():
    """Testing working dir"""
    WorkingDir(Path("tests/resources/workingdir/"))


@patch("shutil.copytree")
def test_copy_template(copytree: callable):
    """Testing working dir"""
    workdir = WorkingDir(Path("anypath"))
    workdir.copy_template()
    copytree.assert_called()


@patch("shutil.copytree")
def test_working_compare_zip_fail(_):
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/a.zip"))
    assert not workdir.compare_to_template()


def test_working_requires_file():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir/"))
    assert workdir.requires_file("API/workingdir.yaml")
    assert not workdir.requires_file("API/notfound.json")


def test_working_get_file():
    """Testing working dir"""
    workpath = "tests/resources/workingdir/"
    workdir = WorkingDir(Path(workpath))
    filepath = "API/workingdir.yaml"
    assert workdir.get_file(filepath) == Path(workpath) / Path(filepath)


def test_working_str():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir/"))
    workstr = str(workdir)
    assert "API/" in workstr
    assert "is_zip: False" in workstr


def test_working_zip():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir.zip"))
    workstr = str(workdir)
    assert "API/workingdir.yaml" in workstr
    assert "is_zip: True" in workstr


def test_working_create_zip():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir/"))
    with patch("zipfile.ZipFile") as file:
        workdir.create_zip("anything.zip")
        file.assert_called()


def test_working_create_zip_failed():
    """Testing working dir"""
    workdir = WorkingDir(Path("willNotBeUsed"))
    with patch("zipfile.ZipFile") as file:
        workdir.create_zip("anything")
        file.assert_not_called()


def test_working_create_zip_failed_2():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir"))
    with patch("zipfile.ZipFile") as file:
        workdir.create_zip("tests/resources/workingdir.zip")
        file.assert_not_called()


def test_working_create_zip_failed_3():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/test"))
    response = workdir.create_zip("tests/resources/workingdir.zip")
    assert not response


def test_working_create_zip_copy():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir.zip"))
    with patch("shutil.copy") as file:
        workdir.create_zip("anything.zip")
        file.assert_called()

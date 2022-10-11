from pathlib import Path
import logging
from Babylon.utils.working_dir import WorkingDir

def test_working_init():
    """Testing working dir"""
    WorkingDir(Path("tests/resources/workingdir/"), logging)

def test_working_compare_1():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir/"), logging)
    assert workdir.compare_to_template()

def test_working_compare_2():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir/"), logging)
    assert workdir.compare_to_template(update_if_error=True)

def test_working_compare_zip():
    """Testing working dir"""
    workdir = WorkingDir(Path("tests/resources/workingdir.zip"), logging)
    assert workdir.compare_to_template()

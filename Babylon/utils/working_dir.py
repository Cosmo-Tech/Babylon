import os
import pathlib
import shutil
import zipfile
import logging
from typing import Optional

import yaml

from . import TEMPLATE_FOLDER_PATH
from .yaml_utils import compare_yaml_keys
from .yaml_utils import complete_yaml
from .yaml_utils import write_yaml_value

logger = logging.getLogger("Babylon")


class WorkingDir:
    """
    Simple class describing a working_dir for Babylon use
    """

    def __init__(self, working_dir_path: pathlib.Path):
        """
        Initialize the working_dir, if not template_path is given will use the default one.
        :param working_dir_path: Path to the Working_dir
        :param logger: Logger used to write infos
        """
        self.path = working_dir_path
        self.initial_path = self.path
        self.is_zip = self.path.is_file() and self.path.suffix == ".zip"
        if self.is_zip:
            self.zip_file = zipfile.ZipFile(self.path)
            self.path = zipfile.Path(self.zip_file)
        self.template_path = TEMPLATE_FOLDER_PATH / "working_dir_template"

    def copy_template(self):
        """
        Initialize the working_dir by making a copy of the template
        """
        if not self.is_zip:
            shutil.copytree(self.template_path, str(self.path), dirs_exist_ok=True)

    def compare_to_template(self, update_if_error: bool = False) -> bool:
        """
        Check if the current working_dir is valid (aka: has all folders and files required by the template)
        :param update_if_error: Replace error logs by info and update the current working_dir with missing elements
        :return: Is the working_dir valid ?
        """
        _root = pathlib.Path(self.template_path)
        error_level = logging.INFO if update_if_error else logging.ERROR
        has_err = False
        logger.debug(f"Starting check of working_dir found on {self.path}")
        for root, dirs, files in os.walk(self.template_path):
            rel_path = pathlib.Path(os.path.relpath(root, _root))
            local_dir_path = self.path / rel_path
            template_dir_path = _root / rel_path
            logger.debug(f"Starting checks for dir {local_dir_path}")
            if not local_dir_path.exists() and not (rel_path == pathlib.Path(".") and self.is_zip):
                logger.log(error_level, f"MISSING DIR: {local_dir_path}")
                has_err = True
                if update_if_error and not self.is_zip:
                    logger.log(error_level, "CORRECTION :  Creating it")
                    shutil.copytree(template_dir_path, str(local_dir_path), dirs_exist_ok=True)
                continue
            for _f in files:
                f_rel_path = rel_path / pathlib.Path(_f)
                template_file_path = _root / f_rel_path
                local_file_path = self.path / f_rel_path
                if os.path.getsize(_root / f_rel_path) > -1:
                    logger.debug(f"Starting check for file {local_file_path}")
                    if not local_file_path.exists():
                        logger.log(error_level, f"MISSING FILE: {local_file_path}")
                        has_err = True
                        if update_if_error and not self.is_zip:
                            logger.log(error_level, "CORRECTION:   Copying it from template")
                            shutil.copy(template_file_path, str(local_file_path))
                    elif local_file_path.name.endswith(".yaml"):
                        logger.debug(f"{f_rel_path} is a yaml file, checking for missing/superfluous keys")
                        missing_keys, superfluous_keys = compare_yaml_keys(template_file_path, local_file_path)
                        if missing_keys:
                            has_err = True
                            logger.log(error_level, f"YAML: In file {local_file_path}")
                            logger.log(error_level, "            The following keys are missing :")
                            for _k in missing_keys:
                                logger.log(error_level, f"            - {_k}")
                            if update_if_error and not self.is_zip:
                                logger.log(error_level, "CORRECTION: Adding them")
                                complete_yaml(template_file_path, local_file_path)
                        if superfluous_keys:
                            logger.debug(f"YAML ISSUE: In file {local_file_path}")
                            logger.debug("            The following keys are superfluous :")
                            for _k in superfluous_keys:
                                logger.debug(f"            - {_k}")
        logger.debug(f"Finished check of working_dir found on {self.path}")
        return not has_err

    def requires_file(self, file_path: str) -> bool:
        return self.get_file(file_path).exists()

    def requires_yaml_key(self, yaml_path: str, yaml_key: str) -> bool:
        v = self.get_yaml_key(yaml_path, yaml_key)
        return v is not None

    def get_yaml_key(self, yaml_path: str, yaml_key: str) -> Optional[object]:
        """
        Will get a key from a yaml in the working_dir
        :param yaml_path: path to the yaml file in the working_dir
        :param yaml_key: key to get in the yaml
        :return: the content of the yaml key
        """
        if not self.requires_file(yaml_path):
            return None
        try:
            _y = yaml.safe_load(self.get_file(yaml_path).open())
            _v = _y[yaml_key]
            return _v
        except (IOError, KeyError):
            return None

    def set_yaml_key(self, yaml_path: str, yaml_key: str, var_value) -> None:
        """
        Set key value in current deployment configuration file
        :param yaml_path: path to the yaml file in the working_dir
        :param yaml_key: key to get in the yaml
        :param var_value: the value to assign
        """
        if not (_path := self.get_file(yaml_path)).exists():
            return
        write_yaml_value(_path, yaml_key, var_value)

    def get_file(self, file_path: str) -> pathlib.Path:
        """
        Will return the effective path of a file in the working_dir
        :param file_path: the relative path of the file in the working_dir
        :return: the path to the file
        """
        target_file_path = self.path / pathlib.Path(file_path)
        return target_file_path

    def __str__(self):
        _ret = [
            f"Template path: {self.template_path}", f"Working_dir path: {self.initial_path.resolve()}",
            f"is_zip: {self.is_zip}", "content:"
        ]
        content = []
        if self.is_zip:
            for _f in self.zip_file.namelist():
                content.append(f"  - {_f}")
        else:
            _r = str(self.path)
            for root, dirs, files in os.walk(str(self.path)):
                rel_path = os.path.relpath(root, _r)
                if rel_path != ".":
                    content.append(f"  - {rel_path}/")
                for _f in files:
                    content.append(f"  - {'' if rel_path == '.' else rel_path + '/'}{_f}")
        _ret.extend(sorted(content))
        return "\n".join(_ret)

    def create_zip(self, zip_path: str, force_overwrite: bool = False) -> Optional[str]:
        """
        Create a zip file of the working_dir to the given path
        :param zip_path: A path to zip the working_dir (if a folder is given will name the zip "working_dir.zip"
        :param force_overwrite: should existing path be ignored and replaced ?
        :return: The effective path of the zip
        """
        _p = pathlib.Path(zip_path)
        if _p.is_dir():
            _p = _p / pathlib.Path("working_dir.zip")
        if _p.exists():
            logger.warning("Target path already exists.")
            if not force_overwrite:
                logger.warning("Abandoning zipping process.")
                return None
        if _p.suffix != ".zip":
            logger.error(f"{_p} is not a correct zip file name")
            return None
        if self.is_zip:
            shutil.copy(str(self.path)[:-1], _p)
        else:
            with zipfile.ZipFile(_p, "w") as _z_file:
                for root, dirs, files in os.walk(str(self.path)):
                    for _f in files:
                        _z_file.write(os.path.join(root, _f), os.path.relpath(os.path.join(root, _f), str(self.path)))
        return str(_p)

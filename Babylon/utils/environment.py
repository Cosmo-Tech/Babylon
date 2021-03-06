import os
import pathlib
import shutil
import zipfile
from logging import Logger
from typing import Union

import yaml


class Environment:
    """
    Simple class describing an environment for Babylon use
    """

    def __init__(self, path: str, logger: Logger, template_path: Union[str, None] = None):
        """
        Initialize the environment, if not template_path is given will use the default one.
        :param path: Path to the Environment
        :param logger: Logger used to write infos
        :param template_path: Optional path to the template against which we want to compare the current Environment
        """
        self.path = pathlib.Path(path)
        self.is_zip = self.path.is_file() and self.path.suffix == ".zip"
        if self.is_zip:
            self.zip_file = zipfile.ZipFile(self.path)
            self.path = zipfile.Path(self.zip_file)
        self.logger = logger
        if template_path is None:
            self.template_path = pathlib.Path(__file__).parent / "EnvironmentTemplate"
        else:
            self.template_path = pathlib.Path(template_path)

    @staticmethod
    def __compare_yaml_keys(template_yaml: pathlib.Path, target_yaml: pathlib.Path) -> tuple[set, set]:
        """
        Compare two yaml files and return the different keys they contain
        :param template_yaml: Yaml file considered as the main file
        :param target_yaml: Yaml file to be compared to the template
        :return: 2 sets of keys :</br>
        - missing_keys : the keys from the template missing from the target</br>
        - superfluous_keys: the keys from the target that are not in the template
        """
        with template_yaml.open() as _te, target_yaml.open() as _ta:
            _template = yaml.safe_load(_te)
            _target = yaml.safe_load(_ta)
            try:
                _template_keys = set(_template.keys())
            except AttributeError:
                _template_keys = set()
            try:
                _target_keys = set(_target.keys())
            except AttributeError:
                _target_keys = set()
            missing_keys = _template_keys - _target_keys
            superfluous_keys = _target_keys - _template_keys
            return missing_keys, superfluous_keys

    @staticmethod
    def __complete_yaml(template_yaml: pathlib.Path, target_yaml: pathlib.Path):
        """
        Will add missing element from template in target
        :param template_yaml: Yaml file considered as the main file
        :param target_yaml: Yaml file to be compared to the template
        :return: Nothing
        """
        with template_yaml.open() as _te, target_yaml.open() as _ta:
            _template = yaml.safe_load(_te)
            _target = yaml.safe_load(_ta)
            try:
                for k, v in _template.items():
                    try:
                        _target.setdefault(k, v)
                    except AttributeError:
                        _target = dict()
                        _target.setdefault(k, v)
            except AttributeError:
                pass
        with target_yaml.open("w") as _ta:
            yaml.safe_dump(_target, _ta)

    def copy_template(self):
        """
        Initialize the environment by making a copy of the template
        :return: Nothing
        """
        if not self.is_zip:
            shutil.copytree(self.template_path, str(self.path), dirs_exist_ok=True)

    def compare_to_template(self, update_if_error: bool = False) -> bool:
        """
        Check if the current environment is valid (aka: has all folders and files required by the template)
        :param update_if_error: Replace error logs by info and update the current environment with missing elements
        :return: Is the environment valid ?
        """
        _root = pathlib.Path(self.template_path)
        error_logger = self.logger.error
        if update_if_error:
            error_logger = self.logger.info
        has_err = False
        self.logger.debug(f"Starting check of environment found on {self.path}")
        for root, dirs, files in os.walk(self.template_path):
            rel_path = pathlib.Path(os.path.relpath(root, _root))
            local_dir_path = self.path / rel_path
            template_dir_path = _root / rel_path
            self.logger.debug(f"Starting checks for dir {local_dir_path}")
            if not local_dir_path.exists() and not (rel_path == pathlib.Path(".") and self.is_zip):
                error_logger(f"MISSING DIR: {local_dir_path}")
                has_err = True
                if update_if_error and not self.is_zip:
                    error_logger("CORRECTION :  Creating it")
                    shutil.copytree(template_dir_path, str(local_dir_path), dirs_exist_ok=True)
                continue
            for _f in files:
                f_rel_path = rel_path / pathlib.Path(_f)
                template_file_path = _root / f_rel_path
                local_file_path = self.path / f_rel_path
                if os.path.getsize(_root / f_rel_path) > -1:
                    self.logger.debug(f"Starting check for file {local_file_path}")
                    if not local_file_path.exists():
                        error_logger(f"MISSING FILE: {local_file_path}")
                        has_err = True
                        if update_if_error and not self.is_zip:
                            error_logger(f"CORRECTION:   Copying it from template")
                            shutil.copy(template_file_path, str(local_file_path))
                    elif local_file_path.name.endswith(".yaml"):
                        self.logger.debug(f"{f_rel_path} is a yaml file, checking for missing/superfluous keys")
                        missing_keys, superfluous_keys = self.__compare_yaml_keys(template_file_path,
                                                                                  local_file_path)
                        if missing_keys:
                            has_err = True
                            error_logger(f"YAML ERROR: In file {local_file_path}")
                            error_logger(f"            The following keys are missing :")
                            for _k in missing_keys:
                                error_logger(f"            - {_k}")
                            if update_if_error and not self.is_zip:
                                error_logger("CORRECTION: Adding them")
                                self.__complete_yaml(template_file_path, local_file_path)
                        if superfluous_keys:
                            self.logger.debug(f"YAML ISSUE: In file {local_file_path}")
                            self.logger.debug(f"            The following keys are superfluous :")
                            for _k in superfluous_keys:
                                self.logger.debug(f"            - {_k}")
        self.logger.debug(f"Finished check of environment found on {self.path}")
        return not has_err

    def requires_file(self, file_path: str) -> bool:
        return self.get_file(file_path).exists()

    def requires_yaml_key(self, yaml_path: str, yaml_key: str) -> bool:
        v = self.get_yaml_key(yaml_path, yaml_key)
        return v is not None

    def get_yaml_key(self, yaml_path: str, yaml_key: str):
        target_file_path = self.get_file(yaml_path)
        try:
            _y = yaml.safe_load(target_file_path.open())
            _v = _y[yaml_key]
            return _v
        except:
            return None

    def get_file(self, file_path: str):
        target_file_path = self.path / pathlib.Path(file_path)
        return target_file_path

    def __str__(self):
        _ret = [f"Template path: {self.template_path}",
                f"Environment path: {self.path}",
                f"is_zip: {self.is_zip}",
                "content:"]
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

    def create_zip(self, zip_path: str, force_overwrite: bool = False) -> Union[str, None]:
        """
        Create a zip file of the environment to the given path
        :param zip_path: A path to zip the environment (if a folder is given will name the zip "Environment.zip"
        :param force_overwrite: should existing path be ignored and replaced ?
        :return: The effective path of the zip
        """
        _p = pathlib.Path(zip_path)
        if _p.is_dir():
            _p = _p / pathlib.Path("Environment.zip")
        if _p.exists():
            self.logger.warning("Target path already exists.")
            if not force_overwrite:
                self.logger.warning("Abandoning zipping process.")
                return None
        if _p.suffix != ".zip":
            self.logger.error(f"{_p} is not a correct zip file name")
            return None
        if self.is_zip:
            shutil.copy(str(self.path)[:-1], _p)
        else:
            with zipfile.ZipFile(_p, "w") as _z_file:
                for root, dirs, files in os.walk(str(self.path)):
                    for _f in files:
                        _z_file.write(os.path.join(root, _f),
                                      os.path.relpath(os.path.join(root, _f),
                                                      str(self.path)))
        return str(_p)

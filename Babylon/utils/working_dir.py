import io
import os
import json
import logging
import pathlib
import shutil
import zipfile
import yaml

from typing import Any
from typing import Optional
from typing import Union
from cryptography.fernet import Fernet
from . import ORIGINAL_TEMPLATE_FOLDER_PATH
from . import ORIGINAL_CONFIG_FOLDER_PATH
from Babylon.utils.yaml_utils import write_yaml_value
from Babylon.utils.yaml_utils import set_nested_key

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
        self.original_template_path = ORIGINAL_TEMPLATE_FOLDER_PATH / "working_dir/.templates"
        self.original_config_dir = ORIGINAL_CONFIG_FOLDER_PATH
        self.template_path = self.path / ".templates"
        self.payload_path = self.path / ".payload"
        self.dtdl_path = self.path / "dtdl"
        self.powerbi_path = self.path / "powerbi"
        self.adx_path = self.path / "adx"
        self.updates_path = self.path / ".updates"
        self.encoding_key = None

    def copy_templates(self):
        """
        Initialize the working_dir by making a copy of the template
        """
        if not self.is_zip:
            shutil.copytree(self.original_template_path, str(self.path / ".templates"), dirs_exist_ok=True)

    def requires_file(self, file_path: str) -> bool:
        return self.get_file(file_path).exists()

    def requires_yaml_key(self, yaml_path: str, yaml_key: str) -> bool:
        v = self.get_yaml_key(yaml_path, yaml_key)
        return bool(v)

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

    def set_yaml_key(self, yaml_path: str, yaml_key: str, var_value: Any) -> None:
        """
        Set key value in current deployment configuration file
        :param yaml_path: path to the yaml file in the working_dir
        :param yaml_key: key to get in the yaml
        :param var_value: the value to assign
        """
        if not (_path := self.get_file(yaml_path)).exists():
            return
        write_yaml_value(_path, yaml_key, var_value)

    def set_encrypted_yaml_key(self, yaml_path: str, yaml_key: Union[list[str], str], var_value: Any) -> None:
        """
        Set key value in an encrypted file
        :param yaml_path: path to the yaml file in the working_dir
        :param yaml_key: key to get in the yaml
        :param var_value: the value to assign
        """
        content = self.get_file_content(yaml_path)
        content = set_nested_key(content, yaml_key, var_value)
        stream = io.StringIO()
        yaml.dump(content, stream)
        raw_content = stream.getvalue().encode("utf-8")
        self.encrypt_file(pathlib.Path(yaml_path), raw_content, override=True)

    def get_file(self, file_path: str) -> pathlib.Path:
        """
        Will return the effective path of a file in the working_dir
        :param file_path: the relative path of the file in the working_dir
        :return: the path to the file
        """
        target_file_path = self.path / pathlib.Path(file_path)
        return target_file_path

    def get_file_content(self, file_path: str) -> Any:
        """
        Return the content of a file from the working dir
        :param file_path: the path to the file inside the working dir
        :return: a dump of the file content in python object
        """
        readers = {".json": json.load, ".yaml": yaml.safe_load}
        _path = self.get_file(file_path)
        reader = readers.get(_path.suffix, None)
        with open(_path) as _f:
            if reader:
                return reader(_f)
            if _path.suffix == ".encrypt":
                content = self.decrypt_file(pathlib.Path(file_path))
                ext = os.path.splitext(os.path.splitext(file_path)[0])[1]
                reader = readers.get(ext)
                if not reader:
                    logger.error(f"Could not read encrypted file of extension {ext}")
                    return {}
                return readers.get(ext)(content) or {}
            return list(_l for _l in _f)

    def __str__(self):
        _ret = [
            f"Template path: {self.original_template_path}", f"Working_dir path: {self.initial_path.resolve()}",
            f"is_zip: {self.is_zip}", "content:"
        ]
        content = []
        if self.is_zip:
            for _f in self.zip_file.namelist():
                content.append(f"  - {_f}")
        else:
            _r = str(self.path)
            for root, _, files in os.walk(str(self.path)):
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
                for root, _, files in os.walk(str(self.path)):
                    for _f in files:
                        _z_file.write(os.path.join(root, _f), os.path.relpath(os.path.join(root, _f), str(self.path)))
        return str(_p)

    def load_secret_key(self):
        try:
            path = self.get_file(".secret.key")
            with open(path, "rb") as f:
                self.encoding_key = f.read()
        except OSError:
            logger.warning(
                "Could not found .secret.key, generate a new one with 'babylon working-dir generate-secret-key'")
            raise ValueError(".secret.key file could not be opened")

    def generate_secret_key(self, override: bool = False) -> pathlib.Path:
        generated_key = Fernet.generate_key()
        self.encoding_key = generated_key
        logger.info(f"Generated new secret key: {generated_key.decode('utf-8')}")
        logger.info("keep that secret securely")
        logger.info(f"export BABYLON_ENCODING_KEY={generated_key.decode('utf-8')}")

    @staticmethod
    def encrypt_content(encoding_key: bytes, content: bytes) -> bytes:
        encoder = Fernet(encoding_key)
        return encoder.encrypt(content)

    @staticmethod
    def decrypt_content(encoding_key: bytes, content: bytes) -> bytes:
        if not content:
            return b""
        try:
            decoder = Fernet(encoding_key)
            data = decoder.decrypt(content)
        except Exception:
            logger.error("Could not decrypt content, wrong key ?")
            return b""
        return data

    def decrypt_file(self, file_name: pathlib.Path) -> Any:
        """
        Use the secret key to decrypt a file
        :param file_name: the file to decrypt
        :return: the decrypted content
        """
        if not self.encoding_key:
            try:
                self.load_secret_key()
            except ValueError:
                logger.error("Can't decrypt a file without the key.")
                return ""
        if not self.get_file(str(file_name)).exists():
            logger.error("File does not exists")
            return ""
        with open(self.get_file(str(file_name)), "rb") as f:
            content = f.read()
            decrypted_content = self.decrypt_content(self.encoding_key, content)
        return decrypted_content

    def encrypt_file(self, file_name: pathlib.Path, content: bytes, override: bool = False) -> pathlib.Path:
        """
        Use the secret key to encrypt the content to a file.
        :param file_name: the target file name after encryption
        :param content: the content to be encrypted
        :param override: Should an existing file be replaced ?
        :return: The effective path of the encrypted file
        """
        if self.get_file(str(file_name)).exists() and not override:
            raise ValueError("File already exists")

        if not self.encoding_key:
            try:
                self.load_secret_key()
            except ValueError:
                self.generate_secret_key()

        encoded_content = self.encrypt_content(self.encoding_key, content)

        with open(self.get_file(str(file_name)), "wb") as f:
            f.write(encoded_content)

        return self.get_file(str(file_name))

import logging
import pathlib

from cryptography.fernet import Fernet

from . import ORIGINAL_CONFIG_FOLDER_PATH, ORIGINAL_TEMPLATE_FOLDER_PATH

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
        self.files_to_deploy = []
        self.initial_path = working_dir_path
        self.original_template_path = ORIGINAL_TEMPLATE_FOLDER_PATH / "working_dir" / ".templates"
        self.original_config_dir = ORIGINAL_CONFIG_FOLDER_PATH
        self.template_path = working_dir_path / ".templates"
        self.encoding_key = None

    def generate_secret_key(self, override: bool = False) -> pathlib.Path:
        generated_key = Fernet.generate_key()
        self.encoding_key = generated_key
        logger.info(f"Generated new secret key: {generated_key.decode('utf-8')}")
        logger.info("keep that secret securely")
        logger.info(f"export BABYLON_ENCODING_KEY={generated_key.decode('utf-8')}")

    def encrypt_content(encoding_key: bytes, content: bytes) -> bytes:
        encoder = Fernet(encoding_key)
        return encoder.encrypt(content)

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

    def append_deployment_file(self, path_file: pathlib.Path):
        mtime = pathlib.Path(path_file).stat().st_mtime
        self.files_to_deploy.append(dict(file=path_file.name, mtime=mtime))

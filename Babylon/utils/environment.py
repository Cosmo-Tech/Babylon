import pathlib
from logging import Logger
import yaml

template = {
    "API": {
        "API_FILES_HERE": ""
    },
    "PowerBI": {
        "POWERBI_FILES_HERE": ""
    },
    "deploy.yaml": """azure_subscription: ""
api_url: ""
api_scope: ""
organization_id: ""
workspace_id: ""
cluster_name: ""
cluster_region: ""
database_name: ""
resource_group_name: ""
"""
}


class Environment:

    def __init__(self, path: str, logger: Logger):
        self.path = pathlib.Path(path)
        self.logger = logger

    def __init_template_element(self, path, content):
        self.logger.debug(f"Creating {path}")
        if type(content) is str:
            with open(path, "w") as f:
                f.write(content)
        else:
            path.mkdir(parents=True)
            for _path, _content in content.items():
                self.__init_template_element(path=path / pathlib.Path(_path), content=_content)

    def __check_template(self, path: pathlib.Path, content, update_if_error: bool = False) -> bool:
        ret = True
        if content != "":
            if path.exists() and path.suffix == ".yaml":
                exisiting = dict(yaml.safe_load(open(path, "r")))
                target = dict(yaml.safe_load(content))
                missing_keys = set(target.keys()) - set(exisiting.keys())
                if missing_keys:
                    message = f"{path} is missing some required keys : {' - '.join(missing_keys)}"
                    if update_if_error:
                        self.logger.debug(message)
                        for k, v in target.items():
                            exisiting.setdefault(k, v)
                        yaml.safe_dump(exisiting, open(path, "w"))
                    else:
                        self.logger.error(message)
                        ret = False
            elif path.exists():
                for _path, _content in content.items():
                    ret = ret and self.__check_template(path=path / pathlib.Path(_path), content=_content,
                                                        update_if_error=update_if_error)
            else:
                if update_if_error:
                    self.logger.debug(f"{path} does not exists")
                    self.__init_template_element(path=path, content=content)
                else:
                    self.logger.error(f"{path} does not exists")
                    ret = False
        if (not update_if_error) and ret:
                self.logger.debug(f"{path} is correct")

        return ret

    def init_template(self):
        try:
            self.path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            self.logger.error(f"{self.path} already exists")
            return
        for _path, _content in template.items():
            self.__init_template_element(path=self.path / pathlib.Path(_path), content=_content)

    def check_template(self, update_if_error: bool = False) -> bool:
        if not self.path.exists():
            if update_if_error:
                self.logger.debug(f"{self.path} does not exists, initializing instead")
                self.init_template()
                return True
            else:
                self.logger.error(f"{self.path} does not exists.")
                return False
        ret = True
        for _path, _content in template.items():
            ret = ret and self.__check_template(path=self.path / pathlib.Path(_path), content=_content,
                                                update_if_error=update_if_error)
        return ret

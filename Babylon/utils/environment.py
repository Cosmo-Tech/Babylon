import pathlib
from logging import Logger
from typing import Union

import yaml

# This template is a simple example of what could be required for a complete version of Babylon
template = {
    "API": {
        "API_FILES_HERE": ""  # Could require a list of yamls representing the api configuration required
    },
    "PowerBI": {
        "POWERBI_FILES_HERE": ""  # Could be a list of pbix files for power bi
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
"""  # This is an example of required elements for Babylon commands
}


class Environment:
    """
    Simple class describing an environment for Babylon use
    """

    def __init__(self, path: str, logger: Logger):
        self.path = pathlib.Path(path)
        self.logger = logger

    def __init_template_element(self, path: pathlib.Path, content: Union[str, dict]):
        """
        Will create an element from the template at given path
        If content is a string, will write a file at path
        Else will create a folder at path and try to create files in content
        :param path: Current path
        :param content: Content to initialise (str or dict)
        :return:
        """
        self.logger.debug(f"Creating {path}")
        if type(content) is str:
            with open(path, "w") as f:
                f.write(content)
        else:
            path.mkdir(parents=True)
            for _path, _content in content.items():
                self.__init_template_element(path=path / pathlib.Path(_path), content=_content)

    def __check_template(self, path: pathlib.Path, content: Union[str, dict], update_if_error: bool = False) -> bool:
        """
        Will check if the current path follows the template
        If path is a yaml file will check for missing keys
        :param path: Current path to check
        :param content: Content that should be present
        :param update_if_error: Mute the error and create/update missing files
        :return: Is the template for path validated at the end of the function
        """
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
                    _r = self.__check_template(path=path / pathlib.Path(_path), content=_content,
                                               update_if_error=update_if_error)
                    ret = ret and _r
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
        """
        Initialize the environment following the template
        :return: Nothing
        """
        try:
            self.path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            self.logger.error(f"{self.path} already exists")
            return
        for _path, _content in template.items():
            self.__init_template_element(path=self.path / pathlib.Path(_path), content=_content)

    def check_template(self, update_if_error: bool = False) -> bool:
        """
        Check if the current environment is valid (aka: has all folders and files required by the template)
        :param update_if_error: Mute errors and update the current environment with missing elements
        :return: Is the enviroment valid ?
        """
        ret = True
        if not self.path.exists():
            if update_if_error:
                self.logger.debug(f"{self.path} does not exists, initializing instead")
                self.init_template()
                return True
            else:
                self.logger.error(f"{self.path} does not exists.")
                ret = False
        for _path, _content in template.items():
            _r = self.__check_template(path=self.path / pathlib.Path(_path), content=_content,
                                       update_if_error=update_if_error)
            ret = ret and _r
        return ret

    def __str__(self):
        _ret = [f"Environment path: {self.path}", ]
        return "\n".join(_ret)

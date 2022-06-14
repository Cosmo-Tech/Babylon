import pathlib

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

    def __init__(self, path, logger):
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

    def init_template(self):
        try:
            self.path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            self.logger.error(f"{self.path} already exists")
            return
        for _path, _content in template.items():
            self.__init_template_element(path=self.path / pathlib.Path(_path), content=_content)

from .configuration import Configuration
from .working_dir import WorkingDir


class Environment:

    def __init__(self, configuration: Configuration, working_dir: WorkingDir):
        self.dry_run = False
        self.configuration = configuration
        self.working_dir = working_dir

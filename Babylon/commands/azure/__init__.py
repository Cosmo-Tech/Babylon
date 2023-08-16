import logging

from click import group as c_group

from Babylon.utils.environment import Environment
from .ad import ad
from .staticwebapp import staticwebapp
from .arm import arm
from .acr import acr
from .adt import adt
from .adx import adx
from .storage import storage
from .appinsight import appinsight
from .permission import permission
from .func import func
from .token import token

logger = logging.getLogger("Babylon")
env = Environment()

list_commands = []
list_groups = [
    ad,
    staticwebapp,
    arm,
    storage,
    acr,
    adt,
    adx,
    appinsight,
    permission,
    func,
    token,
]


@c_group()
def azure():
    """Group allowing communication with Microsoft Azure Cloud"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _group in list_groups:
    azure.add_command(_group)

for _command in list_commands:
    azure.add_command(_command)

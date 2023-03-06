import logging

from click import group as c_group
from .ad import ad
from .staticwebapp import staticwebapp
from .arm import arm
from .acr import acr
from .adt import adt
from .adx import adx
from .storage import storage
from .appinsight import appinsight

logger = logging.getLogger("Babylon")

list_groups = [
    ad,
    staticwebapp,
    arm,
    storage,
    acr,
    adt,
    adx,
    appinsight
]


@c_group()
def azure():
    """Group allowing communication with Microsoft Azure Cloud"""


for _group in list_groups:
    azure.add_command(_group)

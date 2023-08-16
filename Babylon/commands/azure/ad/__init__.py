from click import group as c_group
from .app import app
from .group import group

list_groups = [
    group,
    app,
]


@c_group()
def ad():
    """Azure Active Directory"""


for _group in list_groups:
    ad.add_command(_group)

from setuptools import setup, find_packages
from Babylon.version import get_version

with open('requirements.txt') as f:
    required = f.read().splitlines()

version = get_version()

setup(
    name='Babylon',
    version=version,
    author='Cosmo Tech',
    author_email='nibaldo.donoso@cosmotech.com',
    url="https://github.com/Cosmo-Tech/Babylon",
    description='A CLI made to simplify interaction between Cosmo solutions and Azure',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'console_scripts': ['babylon=Babylon.main:main']},
    install_requires=required,
)

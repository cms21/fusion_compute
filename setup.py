from setuptools import find_packages, setup
from fusion_compute import __version__ as version

install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)

setup(
    name="fusion_compute",
    description="Workflows for Ionorb",
    url='https://github.com/cms21/fusion_compute',
    version=version,
    packages=find_packages(),
    install_requires=install_requires,
    python_requires=">=3.9",
)
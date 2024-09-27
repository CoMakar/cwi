
import os
from setuptools import setup, find_packages
from distutils.command.build import build


class BuildCommand(build):
    def initialize_options(self):
        build.initialize_options(self)
        self.build_base = "setuptools-build"


def load_dotenv(path='.env'):
    if not os.path.exists(path):
        return

    with open(path) as env:
        for line in env:

            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            key, value = line.split('=', 1)
            os.environ[key] = value

load_dotenv()

install_requires = [
    "numpy",
    "pyaudio",
    "loguru",
    "rich",
    "click",
]

dev_requires = [
    "pyinstaller",
]

version = os.getenv("BUILD_VERSION")
name = os.getenv("BUILD_NAME")

setup(
    name=name,
    version=version,
    author="QMakar",
    description="CLI morse audio generator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    
    python_requires=">=3.11",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=install_requires,
    include_package_data=True,
    extras_require={
        "dev": dev_requires,
    },
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: Windows 10 64bit",
    ],
    entry_points={
        "console_scripts": [
            f"{name} = cwi.app:cli",
        ],
    },
    cmdclass={"build": BuildCommand},
)

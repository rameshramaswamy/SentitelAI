# sentinel_shared/setup.py
from setuptools import setup, find_packages

setup(
    name="sentinel_shared",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.0.0",
        "python-json-logger"
    ]
)
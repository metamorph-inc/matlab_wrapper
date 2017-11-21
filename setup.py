from setuptools import setup, find_packages
setup(
    name="matlab_wrapper",
    version="0.1",
    packages=find_packages(),
    install_requires=["openmdao>=1.5.0", "smop>=0.23", "six>=1.10.0"]
)

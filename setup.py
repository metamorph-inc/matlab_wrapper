from setuptools import setup, find_packages
setup(
    name="matlab_wrapper",
    version="0.6",
    packages=find_packages(),
    # FIXME do we need openmdao>=1.5.0,<2.0.0
    install_requires=["openmdao==1.*", "smop>=0.23", "six>=1.10.0"]
)

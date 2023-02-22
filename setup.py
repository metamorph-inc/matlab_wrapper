from setuptools import setup, find_packages
setup(
    name="matlab_wrapper",
    version="0.15",
    packages=find_packages(),
    install_requires=["openmdao>=1.5,<2", "smop>=0.23", "six>=1.10.0"],
    project_urls={
        'Source': 'https://github.com/metamorph-inc/matlab_wrapper',
    },
)

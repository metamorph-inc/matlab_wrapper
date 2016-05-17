from setuptools import setup, find_packages
import py2exe

class Target(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # versioninfo resources
        # self.version = time.strftime("%Y.%m.%d.%H%M%S", _current_time)
        # self.company_name = "Vanderbilt University"
        self.name = "matlab_wrapper_proxy"


setup(
    name="matlab_wrapper",
    version="0.1",
    packages=find_packages(),
    install_requires=["openmdao>=1.6.0", "smop>=0.23", "six>=1.10.0"],
    options={"py2exe": {
                        "dll_excludes": ['w9xpopen.exe', 'API-MS-Win-Core-LocalRegistry-L1-1-0.dll', 'MPR.dll',
                        'libmmd.dll', 'libiomp5md.dll', 'libifcoremd.dll'],
                        "excludes": ["Tkinter"],
                        "bundle_files": 1}},
    console=[Target(script="matlab_wrapper\\proxy.py")]

)

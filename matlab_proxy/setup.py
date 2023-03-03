r"""
Make a 64-bit matlab_proxy (for use with 32-bit Python).

C:\Python27_x64\python -m virtualenv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\python setup.py py2exe
.\venv\Scripts\python setup.py bdist_wheel -p win32
"""

from setuptools import setup, find_packages
import sys
import shutil
import os
import os.path
import platform

if sys.argv[1] == 'py2exe':
    import py2exe

with open('MANIFEST.in', 'w') as manifest:
    if sys.version_info[0] == 2:
        dist_dirs = ['matlab_proxy/dist_27_64bit']
    else:
        dist_dirs = ['matlab_proxy/dist_37_64bit', 'matlab_proxy/dist_39_64bit']
    if 'bdist_wheel' in sys.argv and 'win32' in sys.argv:
        line = 'recursive-include {} *\n'
    else:
        line = 'prune {}\n'
    for dist_dir in dist_dirs:
        manifest.write(line.format(dist_dir))

includes = ["pkgutil", "importlib", "six", "ctypes", "_ctypes"]

if sys.version_info[0:2] == (3, 7):
    includes.append("imp")

setup(
    name="matlab_proxy",
    version="0.17",
    packages=['matlab_proxy'],
    include_package_data=True,
    zip_safe=False,
    options={"py2exe": {
                        # 'xref': True,
                        # 'unbuffered': True,
                        "dll_excludes": ['w9xpopen.exe'],
                        "excludes": """Tkinter tkinter _tkinter tcl tk Tkconstants matlab matlab.engine site doctest
                            _hashlib _socket _ssl bz2 pyexpat select""".split(),
                        "includes": includes,
                        "dist_dir": 'matlab_proxy/dist_' + ''.join((str(v) for v in sys.version_info[0:2])) + '_' + platform.architecture()[0],
                        "unbuffered": True,

                        }},
    zipfile="Python{}{}.zip".format(*sys.version_info[0:2]),
    console=[{
        "dest_base" : "matlab_proxy",
        "script": "matlab_proxy/__init__.py",
    }],
)

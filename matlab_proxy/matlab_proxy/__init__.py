import sys
import six
import pickle
import json
import re
import os
import os.path
import platform
import warnings
import subprocess


class EngineProxyServer(object):
    def __init__(self, engine):
        self.engine = engine

    def addpath(self, path):
        self.engine.addpath(path, nargout=0)

    def invoke(self, name, args, nargout):
        out = six.StringIO()
        err = six.StringIO()
        args = pickle.loads(args)
        outputs = getattr(self.engine, name)(*args, nargout=nargout, stdout=out, stderr=err)

        return {"output": pickle.dumps(outputs), "stdout": out.getvalue(), "stderr": err.getvalue()}

    def quit(self):
        self.engine.quit()


class EngineProxyClient(object):
    def __init__(self, proxy):
        self.proxy = proxy

    def addpath(self, path, nargout=0):
        self.proxy.addpath(path)

    def quit(self):
        self.proxy.quit()
        self.proxy = None

    def __del__(self):
        if self.proxy:
            self.quit()

    def __getattr__(self, name):
        def invoke(*args, **kwargs):
            # (*args, nargout=len(self._output_names), stdout=out, stderr=err)

            ret = self.proxy.invoke(name, pickle.dumps(args), kwargs.get('nargout'))
            for output in ('stdout', 'stderr'):
                stdout = kwargs.get(output)
                if stdout:
                    stdout.write(ret[output])

            return pickle.loads(ret["output"])

        return invoke


def get_matlab_engine():
    if sys.platform == 'win32':
        matlab = get_preferred_matlab()
        if not matlab:
            warnings.warn("MATLAB not found in registry. Using Python implementation.", RuntimeWarning)
            return None
        if matlab[0] == platform.architecture()[0]:
            MATLABROOT = matlab[2]
            engine = import_matlab_python_engine(MATLABROOT)
            return engine.start_matlab()
        else:
            python_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist_{}\\python.exe'.format(matlab[0]))
            if not os.path.isfile(python_exe):
                raise Exception("'{}' does not exist. Run `setup.py py2exe` with Python {} in the matlab_proxy dir".format(python_exe, matlab[0]))
            return get_engine_proxy(matlab[2], python_exe)
    try:
        import matlab.engine
        return matlab.engine.start_matlab()
    except ImportError as e:
        warnings.warn("Failed to import matlab.engine: %s" % e, RuntimeWarning)
        return None


def get_engine_proxy(MATLABROOT, python_exe):
    worker = subprocess.Popen([python_exe, '-E', '-S', '-u', os.path.abspath(__file__), MATLABROOT],
        stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

    magic = worker.stdout.readline().rstrip('\n')
    if magic != HANDSHAKE_MAGIC:
        rest, _ = worker.communicate()
        raise Exception(magic + '\n' + rest)

    def dispatch(method, *args, **kwargs):
        worker.stdin.write(method + '\n')
        worker.stdin.write(json.dumps(args) + '\n')
        worker.stdin.write(json.dumps(kwargs) + '\n')
        e = pickle.loads(json.loads(worker.stdout.readline().rstrip('\n')))
        ret = pickle.loads(json.loads(worker.stdout.readline().rstrip('\n')))
        if e:
            raise e
        return ret

    class Proxy(object):
        def addpath(self, *args, **kwargs):
            return dispatch('addpath', *args, **kwargs)

        def invoke(self, *args, **kwargs):
            return dispatch('invoke', *args, **kwargs)

        def quit(self, *args, **kwargs):
            return dispatch('quit', *args, **kwargs)

    eng = EngineProxyClient(Proxy())

    return eng


def get_preferred_matlab():
    """Return a 3-tuple (arch, version, MATLABROOT) of the latest MATLAB found in the registry."""
    try:
        import _winreg as winreg
    except:
        import winreg

    def get_latest_matlab(reg_wow64):
        try:
            matlab = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\MathWorks\MATLAB', 0, winreg.KEY_READ | reg_wow64)
        except WindowsError as e:
            if e.winerror != 2:
                raise
            return None
        with matlab:
            matlab_versions = []
            try:
                for i in six.moves.range(1000):
                    matlab_versions.append(winreg.EnumKey(matlab, i))
            except WindowsError as e:
                if e.winerror != 259:
                    raise
            matlab_versions.sort(cmp=lambda a, b: -matlab_version_cmp(a, b))
            for matlab_version in matlab_versions:
                with winreg.OpenKey(matlab, matlab_version, 0, winreg.KEY_READ | reg_wow64) as matlab_version_key:
                    try:
                        value, type_ = winreg.QueryValueEx(matlab_version_key, 'MATLABROOT')
                    except WindowsError as e:
                        if e.winerror != 2:
                            raise
                    else:
                        if type_ in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                            return (matlab_version, value)

    m64 = get_latest_matlab(winreg.KEY_WOW64_64KEY)
    m32 = get_latest_matlab(winreg.KEY_WOW64_32KEY)
    if m64 is None and m32 is None:
        return None
    if matlab_version_cmp(m64, m32) == 1 or (matlab_version_cmp(m64, m32) == 0 and platform.architecture()[0] == '64bit'):
        return ('64bit',) + m64
    else:
        return ('32bit',) + m32


def matlab_version_cmp(a, b):
    if a is None and b is None:
        return 0
    if a is None or b is None:
        return cmp(a, b)
    # e.g. R2016a: 9.0
    # R2015aSP1: 8.5.1
    a_match = re.match('(\\d+)\\.(\\d+)(?:\\.(\\d+))?', a)
    b_match = re.match('(\\d+)\\.(\\d+)(?:\\.(\\d+))?', b)
    if a_match is None and b_match is None:
        return cmp(a, b)
    if a_match is None:
        return -1
    if b_match is None:
        return 1
    return cmp([int(x) for x in a_match.groups(0)],
               [int(x) for x in b_match.groups(0)])


def import_matlab_python_engine(MATLABROOT):
    win_bit = {'32bit': 'win32',
            '64bit': 'win64'}[platform.architecture()[0]]
    os.environ['PATH'] += r';{}\bin\{}'.format(MATLABROOT, win_bit)
    sys.path.insert(0, r"{}\extern\engines\python\dist\matlab\engine\{}".format(MATLABROOT, win_bit))
    sys.path.insert(1, r"{}\extern\engines\python\dist".format(MATLABROOT))
    import importlib
    importlib.import_module('matlabengineforpython{}'.format('_'.join(map(str, sys.version_info[0:2]))))
    from matlab import engine
    return engine

HANDSHAKE_MAGIC = 'matlab_\bproxy'

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('MATLABROOT')
    args = parser.parse_args()

    MATLABROOT = args.MATLABROOT

    engine = EngineProxyServer(import_matlab_python_engine(MATLABROOT).start_matlab())
    sys.stdout.write(HANDSHAKE_MAGIC + '\n')

    while True:
        # debug = open('method.txt', 'wb')
        # while True:
        #    debug.write(sys.stdin.readline())
        #    debug.flush()
        method = sys.stdin.readline().rstrip('\n')
        args = sys.stdin.readline().rstrip('\n')
        args = json.loads(args)
        kwargs = json.loads(sys.stdin.readline().rstrip('\n'))
        e = None
        ret = None
        try:
            ret = getattr(engine, method)(*args, **kwargs)
        except Exception as e:
            # import traceback
            # traceback.print_exc(100, open('exception{}.txt'.format(method), 'w'))
            pass

        sys.stdout.write(json.dumps(pickle.dumps(e)) + '\n')
        sys.stdout.write(json.dumps(pickle.dumps(ret)) + '\n')
        sys.stdout.flush()
        if method == 'quit':
            break

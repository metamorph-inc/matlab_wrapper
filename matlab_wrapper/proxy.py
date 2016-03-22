import sys
import six
import pickle
import json
import os.path
from matlab_wrapper.engine import SMOPEngine


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
        self.proxy.addpath('asdf')
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


def get_matlab_engine(is_proxy=False):
    try:
        # TODO test what MATLABs are installed
        # is_64bits = sys.maxsize > 2**32
        # if not no_proxy:
        #    return get_engine_proxy()
        import matlab.engine
        return matlab.engine.start_matlab()
    except ImportError as e:
        import warnings
        if not is_proxy:
            warnings.warn("Failed to import matlab.engine: %s" % e, RuntimeWarning)
        # TODO start server
        return SMOPEngine()


def get_engine_proxy(python_exe=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..\\venv_64\\scripts\\python.exe')):
    import subprocess
    worker = subprocess.Popen([python_exe, '-u', os.path.abspath(__file__)],
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


HANDSHAKE_MAGIC = 'matlab_\bproxy'

if __name__ == '__main__':
    engine = EngineProxyServer(get_matlab_engine(is_proxy=True))
    sys.stdout.write(HANDSHAKE_MAGIC + '\n')

    while True:
        method = sys.stdin.readline().rstrip('\n')
        args = json.loads(sys.stdin.readline().rstrip('\n'))
        kwargs = json.loads(sys.stdin.readline().rstrip('\n'))
        e = None
        ret = None
        try:
            ret = getattr(engine, method)(*args, **kwargs)
        except Exception as e:
            # import traceback
            # traceback.print_exc(100, open('exception.txt', 'w'))
            pass

        sys.stdout.write(json.dumps(pickle.dumps(e)) + '\n')
        sys.stdout.write(json.dumps(pickle.dumps(ret)) + '\n')
        if method == 'quit':
            break

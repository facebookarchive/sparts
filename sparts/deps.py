import imp

def HAS(module):
    try:
        file, pathname, description = imp.find_module(module)
        return imp.load_module(module, file, pathname, description)
    except ImportError:
        return None

HAS_PSUTIL = HAS('psutil')
HAS_THRIFT = HAS('thrift')

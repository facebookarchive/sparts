from contextlib import contextmanager
import shutil
import sys
import tempfile

@contextmanager
def tmpdir(*args, **kwargs):
    path = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield path
    finally:
        shutil.rmtree(path)

@contextmanager
def add_path(path):
    sys.path.append(path)
    try:
        yield path
    finally:
        sys.path.remove(path)

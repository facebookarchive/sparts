from __future__ import absolute_import

from contextlib import contextmanager
from sparts.fileutils import NamedTemporaryDirectory
import sys

@contextmanager
def tmpdir(*args, **kwargs):
    with NamedTemporaryDirectory() as d:
        yield d.name

@contextmanager
def add_path(path):
    sys.path.append(path)
    try:
        yield path
    finally:
        sys.path.remove(path)

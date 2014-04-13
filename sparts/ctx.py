# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module containing various helpful context managers."""
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

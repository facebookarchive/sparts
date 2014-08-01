# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Helpers for commonly performed file operations"""
from distutils.spawn import find_executable
import errno
import fcntl
import logging
import os.path
import shutil
import tempfile

logger = logging.getLogger('sparts.fileutils')


def readfile(path):
    """Return the contents of the file at `path`"""
    with open(path, mode='rb') as f:
        return f.read().decode('UTF-8')

def writefile(path, contents):
    """Write `contents` to the file at `path`"""
    logger.debug('writefile("%s", ...)', path)
    with open(path, mode='wb') as f:
        return f.write(contents.encode('UTF-8'))

def makedirs(path, *args, **kwargs):
    """Create necessary directory heirarchy to `path` if it doesn't exist"""
    try:
        logger.debug('makedirs("%s", ...)', path)
        os.makedirs(path, *args, **kwargs)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise


# This function is really handy.  Make it accessible via this module
find_executable = find_executable


def resolve_partition(path):
    """Return the mount that `path` is present on.

    Requires `psutil`."""
    import psutil
    path = os.path.realpath(path)
    found = None

    for partition in psutil.disk_partitions('all'):
        mountpoint = partition.mountpoint
        if not mountpoint.endswith('/'):
            mountpoint += '/'
        if path.startswith(mountpoint):
            if found is None:
                found = partition
            elif len(mountpoint) > len(found.mountpoint):
                found = partition
    return found


class NamedTemporary(object):
    def __init__(self):
        self.delete = True
        self.close_called = False

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc, value, tb):
        self.close()

    def __str__(self):
        return self.name

    def __repr__(self):
        """Overridden to include the temp dir path for debugging clarity."""
        return "<%s '%s' at 0x%x>" % \
            (self.__class__.__name__, self.name, id(self))

    def close(self):
        """Trigger cleanup (if it has not been disabled)"""
        if not self.close_called:
            if self.delete:
                self._cleanup()
            self.close_called = True

    def keep(self):
        """Request persistence of the contents of this temporary directory.

        Disabled the cleanup logic that is normally triggered on `__exit__()`,
        `__del__()`, or close() calls."""
        self.delete = False

    def _cleanup(self):
        """Implement this to cleanup after yourself"""
        raise NotImplementedError()


class NamedTemporaryDirectory(NamedTemporary):
    """Wrapper around `mkdtemp` that cleans up after itself

    These objects provide the following additional nice features:

    - A `name` attribute, which refers to the full temporary path created
    - The ContextManager protocol, similar to ctx.tempdir,
      to cleanup as the context exits.
    - Implicit cleanup on dereference (via `__del__`)
    - Helpers for reading and writing files relative to this created directory
    """
    def __init__(self, suffix="", prefix=tempfile.template, dir=None):
        self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        super(NamedTemporaryDirectory, self).__init__()

    def _cleanup(self):
        shutil.rmtree(self.name)

    def writefile(self, path, contents):
        """Writes `contents` to the `path` relative to this directory"""
        return writefile(self.join(path), contents)

    def readfile(self, path):
        """Reads the contents from the `path` relative to this directory"""
        return readfile(self.join(path))

    def symlink(self, path, dst):
        """Create a symlink to `dst` at the `path` relative to this directory"""
        return os.symlink(dst, self.join(path))

    def makedirs(self, path):
        return makedirs(self.join(path))

    def join(self, *path):
        return os.path.join(self.name, *path)

def set_nonblocking(fd):
    """Sets O_NONBLOCK on the given `fd`"""
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

from distutils.spawn import find_executable
import os.path
import errno
import logging

logger = logging.getLogger('sparts.fileutils')


def readfile(path):
    with open(path, mode='rb') as f:
        return f.read()

def writefile(path, contents):
    logger.debug('writefile("%s", ...)', path)
    with open(path, mode='wb') as f:
        return f.write(contents)

def makedirs(path, *args, **kwargs):
    try:
        logger.debug('makedirs("%s", ...)', path)
        os.makedirs(path, *args, **kwargs)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise


# This function is really handy.  Make it accessible via this module
find_executable = find_executable


def resolve_partition(path):
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

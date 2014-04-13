# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module related to configuring services under runit"""
import sys
import os.path
from .fileutils import writefile, find_executable, resolve_partition, makedirs
import logging
import stat

logger = logging.getLogger('sparts.runit')

def install(service_name):
    """Installs the running python script as `service_name` under runit."""
    preferred = '/etc/service'
    dirs = get_runsvdir_dirs()
    assert len(dirs) > 0, "runsvdir is not running!"

    if preferred not in dirs:
        preferred = dirs[0]

    service_path = os.path.join(preferred, service_name)
    logger.info('Installing %s in %s', service_name, service_path)
    make_runit_dir(service_name, service_path)

def is_runit_installed():
    """Returns True if runit is installed"""
    # Check if the `runsv` binary is in the path.
    return bool(find_executable('runsv'))

def get_runsvdir_dirs():
    """Returns all dirs being currently managed by `runsvdir`"""
    import psutil
    dirs = []
    # Find all running `runsvdir` processes
    for proc in psutil.process_iter():
        if proc.name == 'runsvdir':
            d = get_runsvdir_dir_from_cmdline(proc.cmdline)
            if d is not None:
                dirs.append(d)
    return dirs

def get_runsvdir_dir_from_cmdline(cmdline):
    """Return runsvdir's target path based on its `cmdline` args"""
    # TODO - unittest this
    for i, arg in enumerate(cmdline):
        # Skip the process name
        if i == 0:
            continue

        # Skip the -P, -H flags
        if arg in ['-P', '-H']:
            continue

        return arg
    return None

def on_same_filesystem(path1, path2):
    """Returns True if `path` and `path2` reside on the same mount"""
    return resolve_partition(path1).mountpoint == \
            resolve_partition(path2).mountpoint

def get_default_args():
    args = sys.argv[:]
    assert len(args) > 0, "Something went horribly wrong"
    assert sys.executable is not None, "Something went horribly wrong"
    args.insert(0, sys.executable)

    # runsv will only redirect standard output to logs.
    # sparts logs stderr only by default.  Let's grab everything
    args.append('2>&1')
    return args

def make_runit_dir(service_name, path, args=None, make_logdir=True):
    # TODO - unittest this
    if args is None:
        args = get_default_args()

    makedirs(path)

    if make_logdir:
        svlogd = find_executable('svlogd')
        assert svlogd is not None, "Unable to make runit dir without svlogd"

        logdir = os.path.join('/var/log', service_name)
        makedirs(logdir)
        make_runit_dir(
            service_name + '.log', os.path.join(path, 'log'),
            args=[svlogd, '-ttv', logdir],
            make_logdir=False
        )

    run_path = os.path.join(path, 'run')
    writefile(run_path, make_run_script_for_args(args))
    flags = os.stat(run_path).st_mode
    os.chmod(run_path, flags | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def make_run_script_for_args(args):
    # TODO - unittest this
    parts = []
    for arg in args:
        if arg == '--runit-install':
            continue

        if os.path.exists(arg):
            parts.append(os.path.realpath(arg))
        else:
            parts.append(arg)

    return "#!/bin/bash\n" + \
        'exec ' + ' '.join(parts)

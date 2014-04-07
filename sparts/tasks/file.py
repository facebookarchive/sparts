# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from .poller import PollerTask
import errno
import os

from ..sparts import option

class DirectoryWatcherTask(PollerTask):
    """DirectoryWatcherTask watches for new, deleted, modified files"""
    PATH = '.'
    path = option(default=lambda cls: cls.PATH,
                  help='Directory path to watch [%(default)s]')
    IGNORE_INITIAL_FILES = True

    def fetch(self):
        d = {}
        root = self.path
        contents = self.listdir(root)
        for name in contents:
            try:
                d[name] = self.stat(os.path.join(root, name))
            except OSError as e:
                # There is a race condition between listdir() and stat() where
                # files might be deleted.  On ENOENT from a stat call, assume
                # the file is gone.  Raise non-ENOENT exceptions
                if e.errno != errno.ENOENT:
                    raise

        return sorted(d.items())

    def listdir(self, path):
        return os.listdir(path)

    def stat(self, path):
        return os.stat(path)

    def onFileCreated(self, filename, stat):
        self.logger.debug('onFileCreated(%s, %s)', filename, stat)

    def onFileDeleted(self, filename, old_stat):
        self.logger.debug('onFileDeleted(%s, %s)', filename, old_stat)

    def onFileChanged(self, filename, old_stat, new_stat):
        self.logger.debug('onFileChanged(%s, %s, %s)', filename, old_stat, new_stat)

    def onValueChanged(self, old_value, new_value):
        if old_value is None:
            # For the first run, ignore pre-existing files by default.
            # Override this class and set this to False if you want them.
            if self.IGNORE_INITIAL_FILES:
                return

            old_value = []
        old_value_dict = dict(old_value)
        new_value_dict = dict(new_value)

        for (name, old_stat) in old_value:
            if name not in new_value_dict:
                self.onFileDeleted(name, old_stat)
            else:
                new_stat = new_value_dict[name]
                if new_stat != old_stat:
                    self.onFileChanged(name, old_stat, new_stat)

        for (name, new_stat) in new_value:
            if name not in old_value_dict:
                self.onFileCreated(name, new_stat)

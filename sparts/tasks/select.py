# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Barebones select-based asynchronous event processor.

You should probably use the twisted, tornado, or other more common async
programming helpers provided by sparts over this."""
from __future__ import absolute_import

from sparts.vtask import VTask
from sparts.fileutils import set_nonblocking

import os
import select


class SelectTask(VTask):
    """A task that runs a select loop with fd registration APIs."""
    DONE = "\x00"
    NEWFD = "\x01"

    def register_read(self, fd, callback):
        """Register `fd` for select.  Will `callback` when readable."""
        assert fd not in self._rcallbacks
        self._rcallbacks[fd] = callback
        self.control(SelectTask.NEWFD)
        self.logger.debug('Registered %s for read on %d', callback, fd)

    def register_write(self, fd, callback):
        """Register `fd` for select.  Will `callback` when writeable."""
        assert fd not in self._wcallbacks
        self._wcallbacks[fd] = callback
        self.control(SelectTask.NEWFD)
        self.logger.debug('Registered %s for write on %d', callback, fd)

    def register_except(self, fd, callback):
        """Register `fd` for select.  Will `callback` when executable."""
        assert fd not in self._xcallbacks
        self._xcallbacks[fd] = callback
        self.control(SelectTask.NEWFD)
        self.logger.debug('Registered %s for except on %d', callback, fd)

    def unregister_read(self, fd):
        """Unregister `fd` from select for read"""
        callback = self._rcallbacks.pop(fd, None)
        self.logger.debug('Unregistered %s from read on %d', callback, fd)
        self.control(SelectTask.NEWFD)
        return callback

    def unregister_write(self, fd):
        """Unregister `fd` from selecting for write"""
        callback = self._wcallbacks.pop(fd, None)
        self.logger.debug('Unregistered %s from write on %d', callback, fd)
        self.control(SelectTask.NEWFD)
        return callback

    def unregister_except(self, fd):
        """Unregister `fd` from selecting for delete"""
        callback = self._xcallbacks.pop(fd, None)
        self.logger.debug('Unregistered %s from except on %d', callback, fd)
        self.control(SelectTask.NEWFD)
        return callback

    def unregister_all(self, fd):
        """Completely unregister `fd` with this event loop."""
        self.unregister_read(fd)
        self.unregister_write(fd)
        self.unregister_except(fd)

    def initTask(self):
        # Flag to check on each iteration
        self._select_running = True

        # Allocate some pipes for meta-select control commands
        self.__rcontrol, self.__wcontrol = os.pipe()
        set_nonblocking(self.__rcontrol)

        # Declare callback lookup dicts
        self._rcallbacks = {}
        self._wcallbacks = {}
        self._xcallbacks = {}

        self.register_read(self.__rcontrol, self._on_control)
        super(SelectTask, self).initTask()

    def control(self, message):
        # Send a control message to the read select pipe
        os.write(self.__wcontrol, message)

    def stop(self):
        super(SelectTask, self).stop()
        self.control(SelectTask.DONE)

    def _select(self):
        # Just calls elect with all the callbacks' fds
        return select.select(
            self._rcallbacks.keys(),
            self._wcallbacks.keys(),
            self._xcallbacks.keys(),
        )

    def _runloop(self):
        # While we should keep running...
        while self._select_running:
            # Select on fds, and execute their callbacks
            rfds, wfds, xfds = self._select()
            self._runcallbacks(xfds, self._xcallbacks)
            self._runcallbacks(rfds, self._rcallbacks)
            self._runcallbacks(wfds, self._wcallbacks)

    def _runcallbacks(self, fds, callbacks):
        # For `fds`, look in `callbacks` for the registered handlers,
        # and execute them.
        for fd in fds:
            if fd in callbacks:
                callbacks[fd](fd)

    def _on_control(self, fd):
        # Internal handler for control messages.
        for c in os.read(fd, 4096):
            if c == SelectTask.DONE:
                self._select_running = False

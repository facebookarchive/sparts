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

import logging
import os
import select
import six
import sys


class SelectTask(VTask):
    """A task that runs a select loop with fd registration APIs."""
    DONE = 0
    NEWFD = 1

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
        """Send a control `message` to the read select pipe"""
        os.write(self.__wcontrol, six.int2byte(message))

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

        os.close(self.__rcontrol)
        os.close(self.__wcontrol)

    def _runcallbacks(self, fds, callbacks):
        """Look in `callbacks` for `fds` registered handlers to execute."""
        for fd in fds:
            if fd in callbacks:
                callbacks[fd](fd)

    def _on_control(self, fd):
        """Internal handler for control messages."""
        for c in six.iterbytes(os.read(fd, 4096)):
            if c == SelectTask.DONE:
                self._select_running = False


class ProcessStreamHandler(object):
    """Helper class for interfacing Popen objects with SelectTask"""
    def __init__(self, popen, select_task,
                 on_stdout=None, on_stderr=None, on_exit=None,
                 encoding=None):

        # Configure a logger first
        self.logger = logging.getLogger('sparts.process_stream_handler')

        # Keep track of inputs (callbacks, proc, fds, select loop, ...)
        self.select_task = select_task
        self._outfd = popen.stdout.fileno()
        self._errfd = popen.stderr.fileno()
        self._popen = popen
        self.stderr_callback = on_stderr
        self.stdout_callback = on_stdout
        self.exit_callback = on_exit

        # Set up a sane default for decoding stdout
        if encoding is None:
            self.logger.debug('Using %s encoding from stdout as default',
                              sys.stdout.encoding)
            self.encoding = sys.stdout.encoding
        else:
            self.encoding = encoding

        # Prepare and connect FDs
        set_nonblocking(self._outfd)
        set_nonblocking(self._errfd)
        self.select_task.register_read(self._outfd, self._on_stdout)
        self.select_task.register_read(self._errfd, self._on_stderr)

    def _on_read(self, callback, fd):
        self.logger.debug('_on_read(%s, %s)', callback, fd)

        data = os.read(fd, 4096)

        if data:
            if callback is not None:
                callback(data.decode(self.encoding))

        else:
            # If os.read() returns "", then there is an error condition
            # e.g., the pipe has been closed
            self._on_exit(fd)

    def _on_stdout(self, fd):
        self._on_read(self.stdout_callback, fd)

    def _on_stderr(self, fd):
        self._on_read(self.stderr_callback, fd)

    def _on_exit(self, fd):
        # Unregister the fd with the select loop
        self.select_task.unregister_read(fd)

        # And set the proper local fd to None
        if fd == self._outfd:
            self._outfd = None
        elif fd == self._errfd:
            self._errfd = None
        else:
            raise Exception("_onexit called with unknown fd, %d" % fd)

        # If both fds have been set to None, it's safe to call the
        # onexit callback (since we've notified the out/err callbacks for
        # all available data)
        if self._errfd is None and self._outfd is None:
            if self.exit_callback:
                self.exit_callback(self._popen.poll())

# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""thrift-related helper tasks"""
from __future__ import absolute_import

from ..vtask import VTask

from sparts.sparts import option
from thrift.server.TNonblockingServer import TNonblockingServer
from thrift.transport.TSocket import TServerSocket

import time


class ThriftHandlerTask(VTask):
    """A loopless task that handles thrift requests.

    You will need to subclass this task, set MODULE, and implement the
    necessary methods in order for requests to be mapped here."""
    LOOPLESS = True
    MODULE = None

    _processor = None

    def initTask(self):
        super(ThriftHandlerTask, self).initTask()
        assert self.MODULE is not None
        self._verifyInterface()

    def _verifyInterface(self):
        iface = self.MODULE.Iface
        missing_methods = []
        for k in dir(iface):
            v = getattr(iface, k, None)
            if not callable(v) or k.startswith('_'):
                continue
            v2 = getattr(self, k, None)
            if v2 is None or not callable(v):
                missing_methods.append(k)

        if missing_methods:
            raise TypeError("%s is missing the following methods: %s" %
                (self.__class__.__name__, missing_methods))

    def _makeProcessor(self):
        return self.MODULE.Processor(self)

    @property
    def processor(self):
        if self._processor is None:
            self._processor = self._makeProcessor()
        return self._processor


class ThriftServerTask(VTask):
    MODULE = None

    def initTask(self):
        super(ThriftServerTask, self).initTask()
        processors = self._findProcessors()
        assert len(processors) > 0, "No processors found for %s" % (self.MODULE)
        assert len(processors) == 1, "Too many processors found for %s" % \
                (self.MODULE)
        self.processorTask = processors[0]

    @property
    def processor(self):
        return self.processorTask.processor

    def _checkTaskModule(self, task):
        """Returns True if `task` implements the appropriate MODULE Iface"""
        # Skip non-ThriftHandlerTasks
        if not isinstance(task, ThriftHandlerTask):
            return False

        # If self.MODULE is None, then connect *any* ThriftHandlerTask
        if self.MODULE is None:
            return True

        iface = self.MODULE.Iface
        # Verify task has all the Iface methods.
        for method_name in dir(iface):
            method = getattr(iface, method_name)

            # Skip field attributes
            if not callable(method):
                continue

            # Check for this method on the handler task
            handler_method = getattr(task, method_name, None)
            if handler_method is None:
                self.logger.debug("Skipping Task %s (missing method %s)",
                                  task.name, method_name)
                return False

            # And make sure that attribute is actually callable
            if not callable(handler_method):
                self.logger.debug("Skipping Task %s (%s not callable)",
                                  task.name, method_name)
                return False

        # If all the methods are there, the shoe fits.
        return True

    def _findProcessors(self):
        """Returns all processors that match this tasks' MODULE"""
        processors = []
        for task in self.service.tasks:
            if self._checkTaskModule(task):
                processors.append(task)
        return processors


class NBServerTask(ThriftServerTask):
    """Spin up a thrift TNonblockingServer in a sparts worker thread"""
    DEFAULT_HOST = '0.0.0.0'
    DEFAULT_PORT = 0
    OPT_PREFIX = 'thrift'

    bound_host = bound_port = None

    host = option(default=lambda cls: cls.DEFAULT_HOST, metavar='HOST',
                  help='Address to bind server to [%(default)s]')
    port = option(default=lambda cls: cls.DEFAULT_PORT,
                  type=int, metavar='PORT',
                  help='Port to run server on [%(default)s]')
    num_threads = option(name='threads', default=10, type=int, metavar='N',
                         help='Server Worker Threads [%(default)s]')

    def initTask(self):
        """Overridden to bind sockets, etc"""
        super(NBServerTask, self).initTask()

        self._stopped = False

        # Construct TServerSocket this way for compatibility with fbthrift
        self.socket = TServerSocket(port=self.port)
        self.socket.host = self.host

        self.server = TNonblockingServer(self.processor, self.socket,
                                         threads=self.num_threads)
        self.server.prepare()

        self.bound_addrs = []
        for handle in self._get_socket_handles(self.server.socket):
            addrinfo = handle.getsockname()
            self.bound_host, self.bound_port = addrinfo[0:2]
            self.logger.info("%s Server Started on %s", self.name,
                self._fmt_hostport(self.bound_host, self.bound_port))

    def _get_socket_handles(self, tsocket):
        """Helper to retrieve the socket objects for a given TServerSocket"""
        handle = getattr(tsocket, 'handle', None)
        if handle is not None:
            return [tsocket.handle]

        # Some TServerSocket implementations support multiple handles per
        # TServerSocket (e.g., to support binding v4 and v6 without
        # v4-mapped addresses
        return tsocket.handles.values()

    def _fmt_hostport(self, host, port):
        if ':' in host:
            return '[%s]:%d' % (host, port)
        else:
            return '%s:%d' % (host, port)

    def stop(self):
        """Overridden to tell the thrift server to shutdown asynchronously"""
        self.server.stop()
        self.server.close()
        self._stopped = True

    def _runloop(self):
        """Overridden to execute TNonblockingServer's main loop"""
        while not self.server._stop:
            self.server.serve()
        while not self._stopped:
            time.sleep(0.1)

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


class ThriftProcessorTask(VTask):
    """A loopless task that helps process thrift requests.

    You will need a subclass of this task in order to properly handle thrift
    requests in your NBServerTasks and such."""
    LOOPLESS = True
    PROCESSOR = None

    def __init__(self, service):
        # TODO: I don't like the way this works: it's too much boilerplate and
        # complexity to implement custom thrift services.
        super(ThriftProcessorTask, self).__init__(service)
        assert self.PROCESSOR is not None
        self.processor = self.PROCESSOR(self.service)


class NBServerTask(VTask):
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

    def getProcessor(self):
        """Automatically find the ThriftProcessorTask subclass"""
        found = None
        for task in self.service.tasks:
            if isinstance(task, ThriftProcessorTask):
                assert found is None, "Multiple processor tasks! (%s, %s)" % \
                    (found.name, task.name)
                found = task
        assert found is not None, "No ThriftProcessorTask's found!"
        return found.processor

    def initTask(self):
        """Overridden to bind sockets, etc"""
        super(NBServerTask, self).initTask()

        self._stopped = False
        self.socket = TServerSocket(self.host, self.port)
        self.server = TNonblockingServer(self.getProcessor(), self.socket,
                                         threads=self.num_threads)
        self.server.prepare()
        self.bound_host, self.bound_port = \
            self.server.socket.handle.getsockname()
        self.logger.info("%s Server Started on %s:%s",
                         self.name, self.bound_host, self.bound_port)

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

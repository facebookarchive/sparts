from __future__ import absolute_import

from ..vtask import VTask

from thrift.server.TNonblockingServer import TNonblockingServer
from thrift.transport.TSocket import TServerSocket

import time


class ThriftProcessorTask(VTask):
    LOOPLESS = True
    PROCESSOR = None 

    def __init__(self, service):
        super(ThriftProcessorTask, self).__init__(service)
        assert self.PROCESSOR is not None
        self.processor = self.PROCESSOR(self.service)


class NBServerTask(VTask):
    DEFAULT_HOST = '0.0.0.0'
    DEFAULT_PORT = 0
    OPT_PREFIX = 'thrift'

    bound_host = bound_port = None

    def getProcessor(self):
        found = None
        for task in self.service.tasks:
            if isinstance(task, ThriftProcessorTask):
                assert found is None, "Multiple processor tasks! (%s, %s)" % \
                    (found.name, task.name)
                found = task
        assert found is not None, "No ThriftProcessorTask's found!"
        return found.processor

    def initTask(self):
        super(NBServerTask, self).initTask()

        self._stopped = False
        self.socket = TServerSocket(
            self.getTaskOption('host'), self.getTaskOption('port'))
        self.server = TNonblockingServer(
            self.getProcessor(), self.socket,
            threads=self.getTaskOption('threads'))
        self.server.prepare()
        self.bound_host, self.bound_port = \
            self.server.socket.handle.getsockname()
        self.logger.info("%s Server Started on %s:%s",
                         self.name, self.bound_host, self.bound_port)

    def stop(self):
        self.server.close()
        self.server.stop()
        self._stopped = True

    def _runloop(self):
        while not self.server._stop:
            self.server.serve()
        while not self._stopped:
            time.sleep(0.1)

    @classmethod
    def _addArguments(cls, ap):
        super(NBServerTask, cls)._addArguments(ap)
        ap.add_argument(cls._loptName('host'), default=cls.DEFAULT_HOST,
                        metavar='HOST',
                        help='Address to bind server to [%(default)s]')
        ap.add_argument(cls._loptName('port'), type=int, metavar='PORT',
                        default=cls.DEFAULT_PORT,
                        help='Port to run server on [%(default)s]')
        ap.add_argument(cls._loptName('threads'), type=int, default=10,
                        metavar='N',
                        help='Server Worker Threads [%(default)s]')

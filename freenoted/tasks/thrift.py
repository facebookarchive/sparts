from __future__ import absolute_import

from ..vtask import VTask

from thrift.server.TNonblockingServer import TNonblockingServer
from thrift.transport.TSocket import TServerSocket
from thrift.Thrift import TProcessor

import time

class NBServerTask(VTask):
    DEFAULT_HOST = '0.0.0.0'
    DEFAULT_PORT = 0
    OPT_PREFIX = 'thrift'

    bound_host = bound_port = None

    def initTask(self):
        super(NBServerTask, self).initTask()

        self._stopped = False
        self.socket = TServerSocket(
            self.getTaskOption('host'), self.getTaskOption('port'))
        self.server = TNonblockingServer(
            self.makeProcessor(), self.socket,
            threads=self.getTaskOption('threads'))
        self.server.prepare()
        self.bound_host, self.bound_port = \
            self.server.socket.handle.getsockname()
        self.logger.info("Server Started on %s:%s",
                         self.bound_host, self.bound_port)

    def makeProcessor(self):
        for inst in [self, self.service]:
            module = getattr(inst, 'THRIFT', None)
            if module is not None:
                if issubclass(module.Processor, TProcessor):
                    return module.Processor(inst)

        raise Exception("Either %s or %s must define THRIFT as a TProcessor" %
                        (self.name, self.service.name))

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

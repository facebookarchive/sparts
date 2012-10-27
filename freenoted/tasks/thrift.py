from __future__ import absolute_import

from ..vtask import VTask

from thrift.server.TNonblockingServer import TNonblockingServer
from thrift.transport.TSocket import TServerSocket
from thrift.Thrift import TProcessor

class NBServerTask(VTask):
    DEFAULT_HOST = '0.0.0.0'
    DEFAULT_PORT = 0
    OPT_PREFIX = 'thrift'

    bound_host = bound_port = None

    def initTask(self):
        super(NBServerTask, self).initTask()

        self.socket = TServerSocket(
            self.getTaskOption('host'), self.getTaskOption('port'))
        self.server = TNonblockingServer(
            self.getProcessor(), self.socket,
            threads=self.getTaskOption('threads'))
        self.server.prepare()
        self.bound_host, self.bound_port = \
            self.server.socket.handle.getsockname()
        self.logger.info("Server Started on %s:%s",
                         self.bound_host, self.bound_port)

    def getProcessor(self):
        if isinstance(self, TProcessor):
            return self
        elif isinstance(self.service, TProcessor):
            return self.service
        else:
            raise Exception("Either %s or %s must subclass TProcessor" %
                            (self.name, self.service.name))

    def stop(self):
        self.server.stop()

    def _runloop(self):
        while not self.server._stop:
            self.server.serve()

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

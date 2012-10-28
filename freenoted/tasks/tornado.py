from __future__ import absolute_import

from ..vtask import VTask, SkipTask

import tornado.ioloop
import tornado.web
import tornado.httpserver

class TornadoIOLoopTask(VTask):
    OPT_PREFIX = 'tornado'

    def initTask(self):
        super(TornadoIOLoopTask, self).initTask()
        needed = getattr(self.service, 'REQUIRE_TORNADO', False)
        for t in self.service.tasks:
            if isinstance(t, TornadoTask):
                needed = True

        if not needed:
            raise SkipTask("No TornadoTasks found or enabled")

        self.ioloop = tornado.ioloop.IOLoop.instance()

    def _runloop(self):
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()


class TornadoTask(VTask):
    def initTask(self):
        super(TornadoTask, self).initTask()
        self.ioloop_task = self.service.requireTask('TornadoIOLoopTask')

    @property
    def ioloop(self):
        return self.ioloop_task.ioloop


class TornadoHTTPTask(TornadoTask):
    LOOPLESS = True
    OPT_PREFIX = 'http'
    DEFAULT_PORT = 0
    DEFAULT_HOST = ''

    @classmethod
    def _addArguments(cls, ap):
        super(TornadoHTTPTask, cls)._addArguments(ap)
        ap.add_argument(cls._loptName('host'), default=cls.DEFAULT_HOST,
                        metavar='HOST',
                        help='Address to bind server to [%(default)s]')
        ap.add_argument(cls._loptName('port'), type=int, metavar='PORT',
                        default=cls.DEFAULT_PORT,
                        help='Port to run server on [%(default)s]')

    def initTask(self):
        super(TornadoHTTPTask, self).initTask()
        self.app = tornado.web.Application(self.getApplicationConfig())
        self.server = tornado.httpserver.HTTPServer(self.app)
        self.server.listen(self.getTaskOption('port'),
                           self.getTaskOption('host'))
        assert len(self.server._sockets) == 1
        for socket in self.server._sockets.itervalues():
            self.bound_host, self.bound_port = socket.getsockname()
        self.logger.info("%s Server Started on %s:%s",
                         self.name, self.bound_host, self.bound_port)

    def stop(self):
        super(TornadoHTTPTask, self).stop()
        self.server.stop()

    def getApplicationConfig(self):
        return [
            ('/', HelloWorldHandler),
        ]

class HelloWorldHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

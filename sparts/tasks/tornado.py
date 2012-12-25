from __future__ import absolute_import

from ..vtask import VTask, SkipTask
from ..sparts import option

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.netutil

import grp
import os


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
        super(TornadoIOLoopTask, self).stop()


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
    DEFAULT_SOCK = ''

    host = option('host', metavar='HOST', default=lambda cls: cls.DEFAULT_HOST,
                  help='Address to bind server to [%(default)s]')
    port = option('port', metavar='PORT', default=lambda cls: cls.DEFAULT_PORT,
                  help='Port to run server on [%(default)s]')
    sock = option('sock', metavar='PATH', default=lambda cls: cls.DEFAULT_SOCK,
                  help='Default path to use for local file socket '
                       '[%(default)s]')
    group = option('sock-group', metavar='GROUP', default='',
                   help='Group to create unix files as [%(default)s]')

    def initTask(self):
        super(TornadoHTTPTask, self).initTask()

        self.app = tornado.web.Application(self.getApplicationConfig())
        self.server = tornado.httpserver.HTTPServer(self.app)

        if self.sock:
            assert self.host == self.DEFAULT_HOST, \
                "Do not specify host *and* sock (%s, %s)" % \
                (self.host, self.sock)
            assert int(self.port) == self.DEFAULT_PORT, \
                "Do not specify port *and* sock (%s, %s)" % \
                (self.port, self.DEFAULT_PORT)

            gid, mode = -1, 0600
            if self.group != '':
                e = grp.getgrnam(self.group)
                gid, mode = e.gr_gid, 0660

            sock = tornado.netutil.bind_unix_socket(self.sock, mode=mode)
            if gid != -1:
                os.chown(self.sock, -1, gid)
            self.server.add_sockets([sock])
        else:
            self.server.listen(self.port, self.host)

        self.bound_addrs = []
        for sock in self.server._sockets.itervalues():
            sockaddr = sock.getsockname()
            self.bound_addrs.append(sockaddr)
            self.logger.info("%s Server Started on %s (port %s)",
                             self.name, sockaddr[0], sockaddr[1])

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

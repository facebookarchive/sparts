# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import
from sparts.tests.base import MultiTaskTestCase, Skip

try:
    from sparts.tasks.thrift import NBServerTask
except ImportError:
    raise Skip("thrift is required to run this test")

from sparts.tasks.fb303 import FB303HandlerTask
from sparts.tasks.tornado import TornadoHTTPTask
from sparts.tasks.tornado_thrift import TornadoThriftHandler

from sparts.thrift.client import ThriftClient
from sparts.gen.fb303 import FacebookService
from sparts.gen.fb303.ttypes import fb_status

import socket
import sys

class ThriftHTTPTask(TornadoHTTPTask):
    def getApplicationConfig(self):
        return [
            ('/thrift', TornadoThriftHandler,
             dict(processor=self.service.tasks.FB303HandlerTask)),
        ]


class TestFB303(MultiTaskTestCase):
    TASKS = [NBServerTask, FB303HandlerTask, ThriftHTTPTask]

    def assertCanConnect(self, host, port):
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((host, port))
        return s

    def testNBServerConnect(self):
        server = self.service.requireTask(NBServerTask)
        self.assertNotNone(server.bound_port)
        self.assertCanConnect('127.0.0.1', server.bound_port)
        return server

    def testNBServerCommand(self):
        server = self.service.requireTask(NBServerTask)
        client = ThriftClient.for_localhost(
                server.bound_port, module=FacebookService)
        self.assertEqual(client.getStatus(), fb_status.ALIVE)

    def testHTTPServerCommand(self):
        server = self.service.tasks.ThriftHTTPTask
        self.assertGreater(len(server.bound_addrs), 0)

        for bound_addr in server.bound_addrs:
            if ':' in bound_addr[0]:
                # IPv6 addresses in URLs are not urlparseable by py2.6
                # So we skip in this case.
                if sys.version < '2.7':
                    continue
                host = '::1'
            else:
                host = '127.0.0.1'

            client = ThriftClient.for_hostport(
                    host=host, port=bound_addr[1],
                    path='/thrift', module=FacebookService)
            self.assertEqual(client.getStatus(), fb_status.ALIVE)

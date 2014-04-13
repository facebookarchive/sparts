# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import
from .base import MultiTaskTestCase, Skip

try:
    import thrift.server
except ImportError:
    raise Skip("thrift is required to run this test")

from sparts.tasks.fb303 import FB303ProcessorTask
from sparts.tasks.thrift import NBServerTask

from sparts.thrift.client import ThriftClient
from sparts.gen.fb303 import FacebookService
from sparts.gen.fb303.ttypes import fb_status

import socket

class TestFB303(MultiTaskTestCase):
    TASKS = [NBServerTask, FB303ProcessorTask]

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
        self.assertEquals(client.getStatus(), fb_status.ALIVE)

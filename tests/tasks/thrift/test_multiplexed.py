# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import

from sparts.tests.base import MultiTaskTestCase, Skip
from sparts.thrift import compiler

# Make sure we have the thrift-runtime related sparts tasks
try:
    from sparts.tasks.thrift.handler import ThriftHandlerTask
    from sparts.tasks.thrift.nbserver import NBServerTask
    from sparts.thrift.client import ThriftClient
except ImportError:
    raise Skip("Need thrift language bindings to run this test")

# Make sure we have the thrift compiler
if compiler.get_executable() is None:
    raise Skip("Need thrift compiler to run this test")

# String containing .thrift file contents for some example services
EXAMPLE_SERVICES = """
service FooService {
    string makeFoos(1: i16 numfoos),
}

service BarService {
    string makeBars(1: i16 numbars),
}
"""

# Compile the above service
SERVICES = compiler.CompileContext().importThriftStr(EXAMPLE_SERVICES)

class FooHandler(ThriftHandlerTask):
    MODULE = SERVICES.FooService
    def makeFoos(self, numfoos):
        return "foo" * numfoos

class BarHandler(ThriftHandlerTask):
    MODULE = SERVICES.BarService
    SERVICE_NAME = 'bar'

    def makeBars(self, numbars):
        return "bar" * numbars

class MultiplexedServer(NBServerTask):
    MULTIPLEX = True

class NonMultiplexedServer(NBServerTask):
    MULTIPLEX = False


class TestMultiplexedServer(MultiTaskTestCase):
    TASKS = [FooHandler, BarHandler, MultiplexedServer]
    
    def testClientWorks(self):
        server = self.service.requireTask(MultiplexedServer)

        # Verify the client and service for FooService/Handler
        client = ThriftClient.for_localhost(
            server.bound_port,
            module=SERVICES.FooService,
            multiplex_service='FooHandler',
        )
        self.assertEqual(
            client.makeFoos(3),
            "foofoofoo",
        )

        # Make sure makeBars does not work for FooService
        with self.assertRaises(Exception):
            client.makeBars(1)

        # Verify the client and service for BarService/Handler
        client = ThriftClient.for_localhost(
            server.bound_port,
            module=SERVICES.BarService,
            multiplex_service='bar',
        )
        self.assertEqual(
            client.makeBars(2),
            "barbar",
        )

        # Make sure makeFoos does not work for BarService
        with self.assertRaises(Exception):
            client.makeFoos(1)

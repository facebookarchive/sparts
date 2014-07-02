# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import MultiTaskTestCase, Skip

try:
    import tornado
except ImportError:
    raise Skip("Tornado must be installed to run this test")

from six.moves.urllib.request import urlopen
from sparts.tasks.tornado import TornadoIOLoopTask, TornadoHTTPTask

class TestURLFetchDemo(MultiTaskTestCase):
    TASKS = [TornadoIOLoopTask, TornadoHTTPTask]

    def test_hello_world(self):
        http = self.service.requireTask('TornadoHTTPTask')
        self.assertNotEmpty(http.bound_addrs)
        for addr in http.bound_addrs:
            self.assertTrue(len(addr) in [2, 4])
            if len(addr) == 4:
                host, port = '[::1]', addr[1]
            else:  # len(addr) == 2
                host, port = '127.0.0.1', addr[1]
            self.logger.debug('hostport = %s:%s', host, port)

            f = urlopen('http://%s:%s/' % (host, port))
            self.assertEqual(f.read().decode('ascii'), 'Hello, world')

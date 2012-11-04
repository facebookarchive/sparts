from sparts.tasks.tornado import TornadoIOLoopTask, TornadoHTTPTask
from ..base import MultiTaskTestCase 
import urllib2

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

            f = urllib2.urlopen('http://%s:%s/' % (host, port))
            self.assertEquals(f.read(), 'Hello, world')

import unittest2

from sparts.vservice import VService


class BaseSpartsTestCase(unittest2.TestCase):
    def assertNotNone(self, o, msg=''):
        self.assertTrue(o is not None, msg)

class SingleTaskTestCase(BaseSpartsTestCase):
    TASK = None
    def setUp(self):
        self.assertNotNone(self.TASK)

        class TestService(VService):
            TASKS=[self.TASK]

        ap = TestService._makeArgumentParser()
        ns = ap.parse_args(['--level', 'DEBUG'])
        self.service = TestService(ns)
        self.runloop = self.service.startBG()
        self.task = self.service.requireTask(self.TASK.__name__)

    def tearDown(self):
        self.service.stop()
        self.runloop.join()

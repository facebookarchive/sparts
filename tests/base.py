import unittest2
import logging

from sparts.vservice import VService


class BaseSpartsTestCase(unittest2.TestCase):
    def assertNotNone(self, o, msg=''):
        self.assertTrue(o is not None, msg)

    def assertNotEmpty(self, o, msg=''):
        self.assertTrue(len(o) > 0, msg)

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger('sparts.%s' % cls.__name__)
        super(BaseSpartsTestCase, cls).setUpClass()

    def assertContains(self, item, arr, msg=''):
        return self.assertIn(item, arr, msg)

class MultiTaskTestCase(BaseSpartsTestCase):
    def requireTask(self, task_name):
        self.assertNotNone(self.service)
        return self.service.requireTask(task_name)

    TASKS = []
    def setUp(self):
        self.assertNotEmpty(self.TASKS)

        class TestService(VService):
            TASKS=self.TASKS

        ap = TestService._makeArgumentParser()
        ns = ap.parse_args(['--level', 'DEBUG'])
        self.service = TestService(ns)
        self.runloop = self.service.startBG()

        for t in self.TASKS:
            self.service.requireTask(t.__name__)

    def tearDown(self):
        self.service.stop()
        self.runloop.join()

class SingleTaskTestCase(MultiTaskTestCase):
    TASK = None

    @classmethod
    def setUpClass(cls):
        if cls.TASK:
            cls.TASKS = [cls.TASK]
        super(SingleTaskTestCase, cls).setUpClass()

    def setUp(self):
        self.assertNotNone(self.TASK)
        MultiTaskTestCase.setUp(self)
        self.task = self.service.requireTask(self.TASK.__name__)

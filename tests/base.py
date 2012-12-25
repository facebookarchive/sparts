import unittest2
import unittest
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

    def setUp(self):
        if not hasattr(unittest.TestCase, 'setUpClass'):
            cls = self.__class__
            if not hasattr(cls, '_unittest2_setup'):
                cls.setUpClass()
                cls._unittest2_setup = 0
            cls._unittest2_setup += 1

    def tearDown(self):
        if not hasattr(unittest.TestCase, 'tearDownClass'):
            cls = self.__class__
            if not hasattr(cls, '_unittest2_setup'):
                cls._unittest2_setup = 0
            else:
                cls._unittest2_setup -= 1
            if cls._unittest2_setup == 0:
                cls.tearDownClass()

    def assertContains(self, item, arr, msg=''):
        return self.assertIn(item, arr, msg)

class MultiTaskTestCase(BaseSpartsTestCase):
    def requireTask(self, task_name):
        self.assertNotNone(self.service)
        return self.service.requireTask(task_name)

    TASKS = []
    def setUp(self):
        super(MultiTaskTestCase, self).setUp()
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
        super(SingleTaskTestCase, cls).setUpClass()
        if cls.TASK:
            cls.TASKS = [cls.TASK]

    def setUp(self):
        self.assertNotNone(self.TASK)
        super(SingleTaskTestCase, self).setUp()
        self.task = self.service.requireTask(self.TASK.__name__)

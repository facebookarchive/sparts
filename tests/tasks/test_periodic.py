from sparts.tasks.periodic import PeriodicTask
from ..base import SingleTaskTestCase 
import time


class MyTask(PeriodicTask):
    INTERVAL = 0.1
    counter = 0

    def execute(self):
        self.counter += 1

class TestMyTask(SingleTaskTestCase):
    TASK = MyTask

    def test_execute_happens(self):
        time.sleep(0.5)
        self.assertGreater(self.task.counter, 3)


class MyMultiTask(MyTask):
    workers = 5

class TestMultiTask(SingleTaskTestCase):
    TASK = MyMultiTask
    def test_multi_execute(self):
        time.sleep(0.5)
        self.assertGreater(self.task.counter, 15)

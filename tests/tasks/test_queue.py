# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import SingleTaskTestCase
from sparts.tasks.queue import QueueTask
from sparts.vtask import TryLater


class MyTask(QueueTask):
    counter = 0

    def execute(self, item, context):
        self.counter += 1


class TestMyTask(SingleTaskTestCase):
    TASK = MyTask

    def test_execute_happens(self):
        self.task.queue.put('foo')
        self.task.queue.put('bar')
        self.task.queue.put('baz')
        self.task.queue.join()
        self.assertEqual(self.task.counter, 3)


class MyRetryTask(QueueTask):
    completed = 0
    retried = 0

    def execute(self, item, context):
        if context.attempt <= 10:
            self.retried += 1
            raise TryLater()
        else:
            self.completed += 1


class TestRetries(SingleTaskTestCase):
    TASK = MyRetryTask

    def test_retries_completed(self):
        self.task.queue.put('foo')
        self.task.queue.put('bar')
        self.task.queue.put('baz')
        self.task.queue.join()
        self.assertEqual(self.task.retried, 30)
        self.assertEqual(self.task.completed, 3)


class TestMultipleWorkers(SingleTaskTestCase):
    class TASK(QueueTask):
        WORKERS = 2
        OPT_PREFIX = 'my-q'

    def test_multiple_workers(self):
        self.assertEqual(len(self.task.threads), 2)

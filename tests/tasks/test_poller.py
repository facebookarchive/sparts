# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tasks.poller import PollerTask
from sparts.tests.base import SingleTaskTestCase


class MyTask(PollerTask):
    INTERVAL = 0.1
    counter = 0
    do_increment = False
    num_changes = 0

    def fetch(self):
        if self.do_increment:
            self.counter += 1
        return self.counter

    def onValueChanged(self, old_value, new_value):
        self.num_changes += 1

class PollerTests(SingleTaskTestCase):
    TASK = MyTask

    def test_value_changed(self):
        self.assertEqual(self.task.getValue(), 0)
        self.assertEqual(self.task.num_changes, 1)  # Change from None => 1

        self.task.execute(None)

        self.assertEqual(self.task.getValue(), 0)
        self.assertEqual(self.task.num_changes, 1)

        # Enable incrementing, and force at least one execution
        self.task.do_increment = True
        self.task.execute(None)
        self.task.do_increment = False

        self.assertGreater(self.task.getValue(), 0)
        self.assertGreater(self.task.num_changes, 1)

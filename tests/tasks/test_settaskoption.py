# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.sparts import option
from sparts.vtask import VTask
from sparts.tests.base import SingleTaskTestCase

class SetOptionTask(VTask):
    LOOPLESS = True
    some_option = option(type=int, default=0)


class SetOptionTaskTests(SingleTaskTestCase):
    TASK = SetOptionTask

    def test_set_option(self):
        self.assertEqual(0, self.task.getTaskOption('some_option'))
        self.task.some_option = 5
        self.assertEqual(5, self.task.getTaskOption('some_option'))

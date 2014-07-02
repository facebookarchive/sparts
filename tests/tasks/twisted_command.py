# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tasks.twisted_command import CommandTask
from sparts.tests.base import SingleTaskTestCase

import threading


class PollerTests(SingleTaskTestCase):
    TASK = CommandTask

    def test_line_buffered(self):
        result = ["", None, threading.Event()]

        def on_stdout(trans, msg):
            result[0] += msg

        def on_exit(reason):
            result[1] = reason
            result[2].set()

        self.task.run(['echo', 'Hello World!'], on_stdout=on_stdout,
                      on_exit=on_exit)

        result[2].wait()
        self.assertEqual(result[0], 'Hello World!')

    # TODO: Current unittest framework has bad subtest isolation.
    # Since each test causes a twisted reactor to start/stop,
    # I can't run more than one test per class file(?)
    """

    def test_unbuffered(self):
        result = ["", None, threading.Event()]

        def on_stdout(self, msg):
            result[0] += msg

        def on_exit(self, reason):
            result[1] = reason
            result[2].set()

        self.task.run(['echo', 'Hello World!'], on_stdout=on_stdout,
                      on_exit=on_exit, line_buffered=False)

        self.assertTrue(result[2].wait(30.0))
        self.assertEqual(result[0], 'Hello World!')
    """

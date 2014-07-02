# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import BaseSpartsTestCase
from sparts.timer import Timer, run_until_true


class TimerTests(BaseSpartsTestCase):
    def testInstance(self):
        t = Timer()

        # Mock the timestamp to some fixed value
        t._time = self.mock.Mock()
        t._time.return_value = 100.0

        # Start the timer.  Elapsed should remain 0.0 before and after start
        self.assertEqual(t.elapsed, 0.0)
        t.start()
        self.assertEqual(t.elapsed, 0.0)

        # Make sure running time is 5s
        t._time.return_value = 105.0
        self.assertEqual(t.elapsed, 5.0)

        # Stop and make sure elapsed time is 5s as well
        t.stop()
        self.assertEqual(t.elapsed, 5.0)

        # Bump time by 5s, but make sure elapsed stays the same
        t._time.return_value = 110.0
        self.assertEqual(t.elapsed, 5.0)

        # Re-stop the timer, which should update stop_time and elapsed to 10s
        t.stop()
        self.assertEqual(t.elapsed, 10.0)

    def testContext(self):
        with Timer() as t:
            # Mock the timestamp to some fixed value
            t._time = self.mock.Mock()
            t._time.return_value = 100.0

            # Context manager should have started the timer, so elapsed
            # should be some big negative number
            self.assertLess(t.elapsed, 0)

            # Restart the timer, so we get good data
            t.start()

            # Start the timer.  Elapsed should remain 0.0 before and after start
            t.start()
            self.assertEqual(t.elapsed, 0.0)

            # Make sure running time is 3s
            t._time.return_value = 103.0
            self.assertEqual(t.elapsed, 3.0)

            # Bump time again, before exiting
            t._time.return_value = 105.0

        # Stop (via exit) and make sure elapsed time is 5s as well
        self.assertEqual(t.elapsed, 5.0)

        # Bump time by 5s, but make sure elapsed stays the same
        t._time.return_value = 110.0
        self.assertEqual(t.elapsed, 5.0)

        # Re-stop the timer, which should update stop_time and  elapsed to 10s
        t.stop()
        self.assertEqual(t.elapsed, 10.0)


class RunUntilTrueTests(BaseSpartsTestCase):
    def testTrue(self):
        run_until_true(lambda: True, timeout=5.0)
        self.assertTrue(True)

    def testTimeout(self):
        with self.assertRaises(Exception):
            run_until_true(lambda: False, timeout=0.1)
        self.assertTrue(True)

# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import

from sparts import daemon
from sparts import timer

from sparts.fileutils import writefile
from sparts.tests.base import BaseSpartsTestCase, Skip
from sparts.deps import HAS_DAEMONIZE
from tempfile import NamedTemporaryFile

import os
import time


class SimpleTestCase(BaseSpartsTestCase):
    def test_read_pid(self):
        with NamedTemporaryFile() as tf:
            writefile(tf.name, '1234')
            self.assertEqual(daemon.read_pid(tf.name, self.logger), 1234)

        self.assertIsNone(daemon.read_pid(tf.name, self.logger))

    def test_status(self):
        # Make sure we can poll a fake pidfile for the unittest process
        with NamedTemporaryFile() as tf:
            writefile(tf.name, str(os.getpid()))
            self.assertTrue(daemon.status(tf.name, self.logger))
        # This should fail since the pidfile is deleted
        self.assertFalse(daemon.status(tf.name, self.logger))

        # We should get an EPERM trying to poll pid
        with NamedTemporaryFile() as tf:
            writefile(tf.name, '1')
            self.assertFalse(daemon.status(tf.name, self.logger))

    def test_kill(self):
        child_pid = os.fork()
        if child_pid == 0:
            # Child - Sleep for 100 seconds.  We'll be killed anyway, but in
            # the event that this test fails, we don't want to leave the
            # orphaned process around forever.
            time.sleep(100)
            self.fail()

        with NamedTemporaryFile() as tf:
            writefile(tf.name, str(child_pid))
            self.assertTrue(daemon.kill(tf.name, self.logger))

        # This should return true because there is no file and therefore
        # the service is already dead
        self.assertTrue(daemon.kill(tf.name, self.logger))

    def test_daemonize(self):
        if not HAS_DAEMONIZE:
            raise Skip("need `daemonize` for this test case")

        def daemon_helper():
            time.sleep(100)
            self.fail()

        with NamedTemporaryFile() as tf:
            # Fork so daemonizing the current process does not mess up with the
            # test suite.
            child_pid = os.fork()
            if child_pid == 0:
                try:
                    daemon.daemonize(daemon_helper, name='sparts_unittest',
                                     pidfile=tf.name, logger=self.logger)
                except SystemExit:
                    # Catch the daemonize library's attempt to sys.exit()
                    pass
            else:

                def checkdaemon():
                    try:
                        return daemon.status(tf.name, self.logger)
                    except ValueError:
                        return False

                # Eliminate the race condition waiting for
                # daemonize.Daemonize() to create *and* write the pid to the
                # pidfile.
                timer.run_until_true(checkdaemon, timeout=1.0)

                self.assertTrue(daemon.status(tf.name, self.logger))
                self.assertTrue(daemon.kill(tf.name, self.logger))

        self.assertFalse(daemon.status(tf.name, self.logger))

# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.fileutils import set_nonblocking
from sparts.tests.base import SingleTaskTestCase
from sparts.tasks.select import SelectTask, ProcessStreamHandler, \
    ProcessFailed

import os
import six
import subprocess
import threading


class TestSelectTask(SingleTaskTestCase):
    TASK = SelectTask

    def test_read_event(self):
        r, w = os.pipe()
        set_nonblocking(r)
        try:
            fired = threading.Event()

            def on_event(fd):
                self.logger.info('on_event(%s)', fd)
                self.assertEqual(fd, r)
                fired.set()

            self.task.register_read(r, on_event)

            os.write(w, six.b('1'))

            fired.wait(3.0)
            self.assertTrue(fired.is_set())

            cb = self.task.unregister_read(r)
            self.assertEqual(cb, on_event)
        finally:
            os.close(r)
            os.close(w)

    def test_write_event(self):
        r, w = os.pipe()
        try:
            fired = threading.Event()

            def on_event(fd):
                self.logger.info('on_event(%s)', fd)
                self.assertEqual(fd, w)
                fired.set()

            self.task.register_write(w, on_event)

            fired.wait(3.0)
            self.assertTrue(fired.is_set())

            cb = self.task.unregister_write(w)
            self.assertEqual(cb, on_event)
        finally:
            os.close(r)
            os.close(w)

    def test_except_event(self):
        try:
            r, w = os.pipe()
            fired = threading.Event()

            def on_event(fd):
                self.logger.info('on_event(%s)', fd)
                self.assertEqual(fd, w)
                fired.set()

            self.task.register_except(w, on_event)
            # TODO: Actually write a test case that can trigger the
            # exceptional circumstances that causes this event to fire.
            cb = self.task.unregister_except(w)
            self.assertEqual(cb, on_event)

        finally:
            os.close(r)
            os.close(w)

    def test_popen_communicate(self):
        future = self.task.popen_communicate(
            'echo hello', shell=True)
        result = future.result(3.0)
        self.assertEqual(result.stdout, 'hello\n')
        self.assertEqual(result.returncode, 0)

    def test_popen_communicate_fail(self):
        future = self.task.popen_communicate(
            'false', shell=True)

        with self.assertRaises(ProcessFailed) as cm:
            future.result(1.0)

        self.assertEqual(cm.exception, future.exception(1.0))
        exception = cm.exception
        result = exception.result

        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')
        self.assertNotEqual(result.returncode, 0)


class TestSelectCommands(SingleTaskTestCase):
    TASK = SelectTask

    def test_basic_popen(self):
        p = subprocess.Popen('echo 123; echo 456 1>&2', shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Locally defined callback to verify stdout callback
        def verify_out(msg):
            self.logger.debug('verify_out(%s)', msg)
            self.assertEqual(msg, "123\n")
        verify_out = self.mock.Mock(wraps=verify_out)

        # Locally defined callback to verify stderr callback
        def verify_err(msg):
            self.logger.debug('verify_err(%s)', msg)
            self.assertEqual(msg, "456\n")
        verify_err = self.mock.Mock(wraps=verify_err)

        # Locally defined callback to verify exit callback
        exited = threading.Event()
        def verify_exit(code):
            self.logger.debug('verify_exit(%s)', code)
            self.assertEqual(code, 0)
            exited.set()
        verify_exit = self.mock.Mock(wraps=verify_exit)

        # Create the handler
        ProcessStreamHandler(p, self.task, on_stdout=verify_out,
            on_stderr=verify_err, on_exit=verify_exit)

        # Wait for the process to exit
        self.logger.debug('waiting for exit...')
        exited.wait(3.0)

        # Check return code, etc.
        self.assertNotNone(p.poll())
        self.assertEqual(p.poll(), 0)
        self.assertTrue(exited.is_set())

        # Assert mocks called correctly
        verify_out.assert_called_once_with("123\n")
        verify_err.assert_called_once_with("456\n")
        verify_exit.assert_called_once_with(0)

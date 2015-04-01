# Copyright (c) 2015, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import MultiTaskTestCase, Skip
try:
    from sparts.tasks.dbus import DBusServiceTask, DBusMainLoopTask
    import dbus
except ImportError:
    raise Skip("dbus support is required to run this test")

from sparts.sparts import option
from random import getrandbits


class BaseTestDBusTask(DBusServiceTask):
    def start(self):
        try:
            self.logger.debug('call start()')
            super(BaseTestDBusTask, self).start()
        except dbus.DBusException as err:
            self.logger.debug('got exception')
            self.acquire_name_error = str(err)


class TestDBusSessionTask(BaseTestDBusTask):
    OPT_PREFIX = 'dbus-session'
    BUS_NAME = 'com.github.facebook.test-{}'.format(getrandbits(32))


class TestDBusSystemTask(BaseTestDBusTask):
    OPT_PREFIX = 'dbus-system'
    BUS_NAME = 'com.github.facebook.systemtest'
    USE_SYSTEM_BUS = True


class TestDBus(MultiTaskTestCase):
    TASKS = [TestDBusSessionTask, DBusMainLoopTask]

    def test_session_bus(self):
        # expecting session task to have been started without error
        t = self.service.getTask(TestDBusSessionTask)
        err = getattr(t, 'acquire_name_error', None)
        self.assertEqual(err, None)

    def test_async_run_ok(self):
        # expecting async task to bump the magic number passed as it's
        # argument
        magic_value = 0xdeadbeef

        def _in_loop_task(arg):
            assert(arg == magic_value)
            return magic_value + 1

        t = self.service.getTask(TestDBusSessionTask)
        ft = t.asyncRun(_in_loop_task, magic_value)
        mod_value = ft.result(100)

        self.assertEqual(mod_value, magic_value + 1)

    def test_async_run_exc(self):
        # expecting an exception to be passed from in loop callback to
        # the caller
        class InLoopException(Exception):
            pass

        def _in_loop_task():
            raise InLoopException()

        t = self.service.getTask(TestDBusSessionTask)
        ft = t.asyncRun(_in_loop_task)

        self.assertRaises(InLoopException, lambda: ft.result(100))


class TestSystemDBus(MultiTaskTestCase):
    TASKS = [TestDBusSystemTask, DBusMainLoopTask]

    def test_system_bus(self):
        # expecting system task to fail due to missing DBus policy
        t = self.service.getTask(TestDBusSystemTask)
        err = getattr(t, 'acquire_name_error', None)
        self.assertNotNone(err)
        self.logger.debug('err: %s', err)
        self.assertTrue(err.startswith('org.freedesktop.DBus.Error.AccessDenied'))

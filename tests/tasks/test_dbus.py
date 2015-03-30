# Copyright (c) 2015, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import MultiTaskTestCase, Skip
try:
    import dbus
    from sparts.tasks.dbus import DBusServiceTask, DBusMainLoopTask
except ImportError:
    raise Skip("dbus support is required to run this test")

from sparts.sparts import option

class TestDBusTask(DBusServiceTask):
    BUS_NAME = 'com.github.facebook.test'


class TestDBusSystemTask(DBusServiceTask):
    BUS_NAME = 'com.github.facebook.systemtest'

    system_bus = option(name='system_bus', default=True)

    def start(self):
        try:
            super(TestDBusSystemTask, self).start()
        except dbus.DBusException as err:
            self.acquire_name_error = str(err)


class TestDBus(MultiTaskTestCase):
    TASKS = [TestDBusTask, DBusMainLoopTask]

    def test_session_bus(self):
        bus = dbus.SessionBus(private=True)
        self.assertTrue(bus.name_has_owner(TestDBusTask.BUS_NAME))


class TestSystemDBus(MultiTaskTestCase):
    TASKS = [TestDBusSystemTask, DBusMainLoopTask]

    def test_system_bus(self):
        # expecting system task to fail due to missing DBus policy
        # file
        t = self.service.getTask(TestDBusSystemTask)
        err = getattr(t, 'acquire_name_error', None)
        self.assertNotNone(err)

        self.assertTrue(err.startswith('org.freedesktop.DBus.Error.AccessDenied'))

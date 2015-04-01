# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module providing tasks that help with dbus integration"""
from __future__ import absolute_import

from sparts.sparts import option
from sparts.vtask import VTask, SkipTask

try:
    from sparts.fb303.dbus import FB303DbusService
    from sparts.tasks.fb303 import FB303HandlerTask
    HAVE_FB303 = True
except ImportError:
    HAVE_FB303 = False

from functools import partial
from concurrent.futures import Future
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import dbus.service
import gobject
import glib
import time

# always init threads before calling any dbus code
glib.threads_init()
gobject.threads_init()
dbus.mainloop.glib.threads_init()


class VServiceDBusObject(dbus.service.Object):
    """DBus interface implementation that exports common VService methods"""
    def __init__(self, dbus_service):
        self.dbus_service = dbus_service
        self.service = self.dbus_service.service
        self.logger = self.dbus_service.logger
        self.path = '/'.join(['', self.service.name, 'sparts'])
        dbus.service.Object.__init__(self, self.dbus_service.bus, self.path)

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='s', out_signature='v')
    def getOption(self, name):
        return self.service.getOption(name)

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='sv', out_signature='')
    def setOption(self, name, value):
        if value == '__None__':
            value = None
        self.service.setOption(name, value)

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='', out_signature='a{sv}')
    def getOptions(self):
        result = {}
        for k, v in self.service.getOptions().iteritems():
            # dbus doesn't support serializing None as a variant
            if v is None:
                v = '__None__'
            result[k] = v
        return result

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='', out_signature='as')
    def listOptions(self):
        return self.service.getOptions().keys()

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='', out_signature='')
    def shutdown(self):
        self.service.shutdown()

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='', out_signature='')
    def restart(self):
        self.service.reinitialize()

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='', out_signature='as')
    def listTasks(self):
        return [t.name for t in self.service.tasks]

    @dbus.service.method(dbus_interface='org.sparts.Service',
                         in_signature='', out_signature='x')
    def uptime(self):
        return int(time.time() - self.service.start_time)


class DBusMainLoopTask(VTask):
    """Configure and run the DBus Main Loop in a sparts task. The loop is
    run in separate thread. Keep in mind that dbus bindings are not
    thread-safe. To avoid problems make sure to perform any dbus calls
    wihin the context of the loop (use DBusTask.asyncRun() to perform
    this in a safe manner)
    """
    THREADS_INITED = False
    mainloop = None

    def initTask(self):
        super(DBusMainLoopTask, self).initTask()
        needed = getattr(self.service, 'REQUIRE_DBUS', False)
        for t in self.service.tasks:
            if isinstance(t, DBusTask):
                needed = True

        if not needed:
            raise SkipTask("No DBusTasks found or enabled")

        self.dbus_loop = DBusGMainLoop(set_as_default=True)
        # using main loop with default context
        self.mainloop = gobject.MainLoop()

    def _runloop(self):
        self.mainloop.run()
        # loop.quit() was called, run() has returned, meaning that
        # the loop no longer needed
        self.mainloop = None

    def stop(self):
        super(DBusMainLoopTask, self).stop()

        if self.mainloop is None:
            return

        if not self.mainloop.is_running():
            return
        self.mainloop.quit()


class DBusTask(VTask):
    """Base Class for Tasks that depend on the DBus Main Loop"""
    DEPS = [DBusMainLoopTask]
    LOOPLESS = True

    def initTask(self):
        super(DBusTask, self).initTask()
        self.mainloop_task = self.service.requireTask(DBusMainLoopTask)

    @property
    def mainloop(self):
        return self.mainloop_task.mainloop

    def asyncRun(self, cb, *args, **kwargs):
        """Helper call to run a callback `cb` within the task's main loop.
        Returns an instance of Future() that can be waited for obtain
        the result of computation. The callback will be run only once.
        """
        def _future_execute(f, cb, *args, **kwargs):
            try:
                # Only execute `cb` if the future wasn't cancelled
                if f.set_running_or_notify_cancel():
                    f.set_result(cb(*args, **kwargs))
            except Exception as e:
                f.set_exception(e)
            # return False so that glib will automatically remove the
            # idle source
            return False

        def _future_cancel(handle, f):
            if f.cancelled():
                glib.source_remove(handle)

        f = Future()
        handle = glib.idle_add(partial(_future_execute, f,
                                       cb, *args, **kwargs))
        f.add_done_callback(partial(_future_cancel, handle))
        return f


class DBusServiceTask(DBusTask):
    """Glue Task for exporting this VService over DBus"""
    OPT_PREFIX = 'dbus'
    BUS_NAME = None
    BUS_CLASS = VServiceDBusObject
    USE_SYSTEM_BUS = False

    bus_name = option(default=lambda cls: cls.BUS_NAME, metavar='NAME',
                      help='Bus Name.  Should be something like '
                           '"com.sparts.AwesomeService"')
    replace = option(action='store_true', type=bool,
        default=False, help='Replace, and enable replacing of this service')
    queue = option(action='store_true', type=bool,
        default=False, help='If not --{task}-replace, will wait to take '
                            'this bus name')
    system_bus = option(action='store_true', type=bool,
                        default=lambda cls: cls.USE_SYSTEM_BUS,
                        help='Use system bus')

    dbus_service = None

    def initTask(self):
        super(DBusServiceTask, self).initTask()

        assert self.bus_name is not None, \
            "You must pass a --{task}-bus-name"

    def _makeBus(self):
        if self.system_bus:
            return dbus.SystemBus(private=True)
        return dbus.SessionBus(private=True)

    def _asyncStartCb(self):
        self.bus = self._makeBus()
        self.dbus_service = dbus.service.BusName(self.bus_name,
                                                 self.bus,
                                                 self.replace,
                                                 self.replace,
                                                 self.queue)
        return True

    def _asyncStart(self):
        res = self.asyncRun(self._asyncStartCb)
        res.result()

    def start(self):
        self._asyncStart()
        self.addHandlers()
        super(DBusServiceTask, self).start()

    def addHandlers(self):
        self.sparts_dbus = self.BUS_CLASS(self)
        if HAVE_FB303:
            task = self.service.getTask(FB303HandlerTask)
            if task is not None:
                self.fb303_dbus = FB303DbusService(
                    self.dbus_service, task, self.service.name)

    def _asyncStopCb(self):
        self.dbus_service = None
        self.bus = None
        return True

    def _asyncStop(self):
        res = self.asyncRun(self._asyncStopCb)
        res.result()
        # self.bus.close()

    def stop(self):
        """Run the bus cleanup code within the context of the main loop. The
        task depends in DBusMainLoopTask, the stop() method will be called
        before DBusMainLoopTask.stop() where loop.quit() is done.
        """
        super(DBusServiceTask, self).stop()
        self._asyncStop()

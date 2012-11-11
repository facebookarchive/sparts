from __future__ import absolute_import

from ..vtask import VTask, SkipTask
from ..sparts import option
from ..fb303.dbus import FacebookDbusService
from .fb303 import FB303ProcessorTask

from dbus.mainloop.glib import DBusGMainLoop
import dbus
import dbus.service
import gobject
import glib
import time


class VServiceDBusObject(dbus.service.Object):
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
        glib.threads_init()
        gobject.threads_init()
        dbus.mainloop.glib.threads_init()
        self.mainloop = gobject.MainLoop()

    def _runloop(self):
        self.mainloop.run()

    def stop(self):
        super(DBusMainLoopTask, self).stop()

        if self.mainloop is None:
            return

        self.mainloop.quit()

        # OK!  Apparently, there is some wonky destructor event handling that
        # seems to work better than just calling .quit() in order to properly
        # return full control of signal handling, threads, etc to the actual
        # main process.
        self.mainloop = None

class DBusTask(VTask):
    def initTask(self):
        super(DBusTask, self).initTask()
        self.mainloop_task = self.service.requireTask('DBusMainLoopTask')

    @property
    def mainloop(self):
        return self.mainloop_task.mainloop


class DBusServiceTask(DBusTask):
    OPT_PREFIX = 'dbus'
    BUS_NAME = None
    LOOPLESS = True
    BUS_CLASS = VServiceDBusObject

    bus_name = option('bus-name', default=lambda cls: cls.BUS_NAME,
                      metavar='NAME',
                      help='Bus Name.  Should be something like '
                           '"com.sparts.AwesomeService"')
    replace = option('replace', action='store_true', type=bool,
        default=False, help='Replace, and enable replacing of this service')
    queue = option('queue', action='store_true', type=bool,
        default=False, help='If not --{task}-replace, will wait to take '
                            'this bus name')

    def initTask(self):
        super(DBusServiceTask, self).initTask()

        assert self.bus_name is not None, \
            "You must pass a --{task}-bus-name"

    def start(self):
        self.bus = dbus.SessionBus(private=True)
        self.dbus_service = dbus.service.BusName(self.bus_name, self.bus,
            self.replace, self.replace, self.queue)
        self.addHandlers()
        super(DBusServiceTask, self).start()

    def addHandlers(self):
        self.sparts_dbus = self.BUS_CLASS(self)
        task = self.service.getTask(FB303ProcessorTask)
        if task is not None:
            self.fb303_dbus = FacebookDbusService(
                self.dbus_service, task.processor, self.service.name)

    def stop(self):
        del(self.dbus_service)
        #self.bus.close()
        super(DBusServiceTask, self).stop()

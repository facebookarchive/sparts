from __future__ import absolute_import

from sparts.vservice import VService
from sparts.tasks.dbus import DBusMainLoopTask, DBusServiceTask
from sparts.tasks.fb303 import FB303ProcessorTask


class MyDBusServiceTask(DBusServiceTask):
    BUS_NAME = 'org.sparts.DBusDemo'

class MyDBusService(VService):
    TASKS=[DBusMainLoopTask, MyDBusServiceTask, FB303ProcessorTask]


if __name__ == '__main__':
    MyDBusService.initFromCLI()

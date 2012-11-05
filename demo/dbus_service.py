from __future__ import absolute_import

from sparts.vservice import VService
from sparts.tasks.dbus import DBusIOLoopTask, DBusServiceTask


class MyDBusServiceTask(DBusServiceTask):
    BUS_NAME = 'org.sparts.DBusDemo'

class MyDBusService(VService):
    TASKS=[DBusIOLoopTask, MyDBusServiceTask]


if __name__ == '__main__':
    MyDBusService.initFromCLI()

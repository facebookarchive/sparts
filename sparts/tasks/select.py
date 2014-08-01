from __future__ import absolute_import

from select import select
from sparts.vtask import VTask
from sparts.fileutils import set_nonblocking

import os

class SelectTask(VTask):
    DONE = "\x00"
    NEWFD = "\x01"

    def initTask(self):
        self._select_running = True
        self.__rcontrol, self.__wcontrol = os.pipe()

        set_nonblocking(self.__rcontrol)

        self._registered = set()
        self._registered.add(self.__rcontrol)
        super(SelectTask, self).initTask()

    def control(self, message):
        os.write(self.__wcontrol, message)

    def stop(self):
        self.control(SelectTask.DONE)

    def _runloop(self):
        while self._select_running:
            fds = list(self._registered)
            rfds, wfds, xfds = select(fds, fds, fds)

            for fd in xfds:
                self.on_executable(fd)

            for fd in rfds:
                if fd == self.__rcontrol:
                    self._on_control()
                else:
                    self.on_readable(fd)

            for fd in wfds:
                self.on_writeable(fd)

    def _on_control(self):
        for c in os.read(self.__rcontrol, 4096):
            if c == SelectTask.DONE:
                self._select_running = False

    def on_readable(self, fd):
        pass

    def on_writeable(self, fd):
        pass

    def on_executable(self, fd):
        pass

    def register_fd(self, fd):
        self._registered.add(fd)
        self.control(SelectTask.NEWFD)

    def unregister_fd(self, fd):
        self._registered.remove(fd)

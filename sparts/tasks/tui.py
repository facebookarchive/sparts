# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.vtask import VTask

import npyscreen


class UITask(VTask):
    SHUTDOWN_ON_FORM_CLOSE = True

    def initTask(self):
        self._first_run = True
        self.app = npyscreen.NPSAppManaged()
        self.app.onStart = self.appStart
        self.app.onInMainLoop = self.__appInMainLoop
        self.app.onCleanExit = self.appCleanExit
        super(UITask, self).initTask()

    def _runloop(self):
        self.app.run()

        # By default, if we exit out of curses mode, shutdown the service
        self.service.shutdown()

    def appStart(self):
        """Override this method to initialize the app.

        This should generally consist of calls to something like:

            self.app.registerForm('main', self.make_form())
            self.app.setNextForm('main')
        """
        raise NotImplementedError()

    def appInMainLoop(self):
        """Called between each screen while the application is running.

        Not called before the first screen. Override at will"""

    def appCleanExit(self):
        """Override to perform cleanup when application exits without error."""
        self.service.shutdown()

    def __appInMainLoop(self):
        """Internal onMainLoop that configures shutdown on first form close."""
        if self._first_run:
            self._first_run = False
            self.app.setNextForm(None)

        self.appInMainLoop()

    def stop(self):
        """npycurses magic to shutdown the app."""
        super(UITask, self).stop()
        if self.app is not None:
            self.app.switchForm(None)

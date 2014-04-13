# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from .periodic import PeriodicTask
from threading import Event


class PollerTask(PeriodicTask):
    """A PeriodicTask oriented around monitoring a single value.
    
    Simply override `fetch`, and the `onValueChanged()` method will be called
    with the old and new values.  Additionally, the `getValue()` method can
    be called by other tasks to block until the values are ready.
    """
    def initTask(self):
        self.current_value = None
        self.fetched = Event()
        super(PollerTask, self).initTask()

    def execute(self, context=None):
        new_value = self.fetch()
        if self.current_value != new_value:
            self.onValueChanged(self.current_value, new_value)
        self.current_value = new_value
        self.fetched.set()

    def onValueChanged(self, old_value, new_value):
        self.logger.debug('onValueChanged(%s, %s)', old_value, new_value)

    def fetch(self):
        self.logger.debug('fetch')
        return None

    def getValue(self, timeout=None):
        self.fetched.wait(timeout)
        return self.current_value

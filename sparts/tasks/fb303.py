# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module related to implementing fb303 thrift handlers"""
from __future__ import absolute_import

from sparts.tasks.thrift import ThriftHandlerTask
from sparts.gen.fb303 import FacebookService
from sparts.gen.fb303.ttypes import fb_status

import threading
import time
from six import StringIO, iteritems


class FB303HandlerTask(ThriftHandlerTask):
    MODULE = FacebookService

    def initTask(self):
        super(FB303HandlerTask, self).initTask()
        self._profile_lock = threading.Lock()

    def getName(self):
        return self.service.name

    def getVersion(self):
        return str(self.service.VERSION)

    def getStatus(self):
        # TODO: DEAD?  STARTING?  STOPPED?
        if self.service._stop:
            return fb_status.STOPPING
        for task in self.service.tasks:
            # Only check LOOPLESS tasks for "dead" threads
            if not task.LOOPLESS:
                for thread in task.threads:
                    if not thread.isAlive():
                        return fb_status.WARNING

        # Return WARNING if there are any registered warnings
        if self.service.getWarnings():
            return fb_status.WARNING
        return fb_status.ALIVE

    def getStatusDetails(self):
        messages = []
        if self.service._stop:
            messages.append('%s is shutting down' % (self.getName()))

        # Check for dead threads
        for task in self.service.tasks:
            if not task.LOOPLESS:
                for thread in task.threads:
                    if not thread.isAlive():
                        messages.append('%s has dead threads!' % task.name)

        # Append any registered warnings
        messages.extend(self.service.getWarnings().values())
        return '\n'.join(messages)

    def getCounters(self):
        result = {}
        for k, v in iteritems(self.service.getCounters()):
            v = v()
            if v is None:
                continue
            result[k] = int(v)
        return result

    def getCounter(self, name):
        result = self.service.getCounter(name)()
        if result is None:
            raise ValueError("%s is None" % (name))
        return int(result)

    def setOption(self, name, value):
        if value == '__None__':
            value = None
        else:
            cur_value = getattr(self.service.options, name)
            if cur_value is not None:
                try:
                    value = cur_value.__class__(value)
                except Exception as e:
                    self.logger.debug('Unable to cast %s to %s (%s)', value,
                                      cur_value.__class__, e)
        self.service.setOption(name, value)

    def getOption(self, name):
        value = self.service.getOption(name)
        if value is None:
            value = '__None__'
        return str(value)

    def getOptions(self):
        result = {}
        for k in self.service.getOptions():
            result[k] = self.getOption(k)
        return result

    def aliveSince(self):
        return self.service.start_time

    def reinitialize(self):
        self.service.restart()

    def shutdown(self):
        self.service.shutdown()

    def getCpuProfile(self, profileDurationInSec):
        try:
            import yappi
        except ImportError:
            # Fallback (but log) if people call this method and we
            # don't have yappi
            self.logger.warning('getCpuProfile called without yappi installed')
            return ''

        # We need to lock this since it muck about with the global python
        # profile hooks.
        with self._profile_lock:
            yappi.start()
            time.sleep(profileDurationInSec)
            yappi.stop()
            stats = yappi.get_func_stats()

        # Save the "pretty" output to a buffer and return the raw string
        # Alternatively, we should return this as JSON and let the caller
        # render it appropriately, but this is fine for now.
        sio = StringIO()
        stats.print_all(out=sio)
        return sio.getvalue()

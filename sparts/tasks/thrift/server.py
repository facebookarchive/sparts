# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Base Task for implementing thrift servers"""
from __future__ import absolute_import

from sparts.vtask import VTask
from sparts.tasks.thrift.handler import ThriftHandlerTask


class ThriftServerTask(VTask):
    MODULE = None

    def initTask(self):
        super(ThriftServerTask, self).initTask()
        processors = self._findProcessors()
        assert len(processors) > 0, \
                "No processors found for %s" % (self.MODULE)
        assert len(processors) == 1, "Too many processors found for %s" % \
                (self.MODULE)
        self.processorTask = processors[0]

    @property
    def processor(self):
        return self.processorTask.processor

    def _checkTaskModule(self, task):
        """Returns True if `task` implements the appropriate MODULE Iface"""
        # Skip non-ThriftHandlerTasks
        if not isinstance(task, ThriftHandlerTask):
            return False

        # If self.MODULE is None, then connect *any* ThriftHandlerTask
        if self.MODULE is None:
            return True

        iface = self.MODULE.Iface
        # Verify task has all the Iface methods.
        for method_name in dir(iface):
            method = getattr(iface, method_name)

            # Skip field attributes
            if not callable(method):
                continue

            # Check for this method on the handler task
            handler_method = getattr(task, method_name, None)
            if handler_method is None:
                self.logger.debug("Skipping Task %s (missing method %s)",
                                  task.name, method_name)
                return False

            # And make sure that attribute is actually callable
            if not callable(handler_method):
                self.logger.debug("Skipping Task %s (%s not callable)",
                                  task.name, method_name)
                return False

        # If all the methods are there, the shoe fits.
        return True

    def _findProcessors(self):
        """Returns all processors that match this tasks' MODULE"""
        processors = []
        for task in self.service.tasks:
            if self._checkTaskModule(task):
                processors.append(task)
        return processors

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
from thrift.TMultiplexedProcessor import TMultiplexedProcessor


class ThriftServerTask(VTask):
    """Base class for various thrift server implementations."""

    # If self.MODULE is specified, it means that we specifically want this
    # server to route requests to a matching ThriftHandler.  This is done
    # so that we can have multiple ThriftServers handling requests for
    # different services within the same process.
    MODULE = None
    MULTIPLEX = False

    def initTask(self):
        super(ThriftServerTask, self).initTask()
        processors = self._findProcessors()
        assert len(processors) > 0, \
                "No processors found for %s" % (self.MODULE)

        if not self.MULTIPLEX:
            # For non-multiplexed services, we can only have one processor
            # that matches the module.
            assert len(processors) == 1, (
                "Too many processors found for %s.  Did you mean to set " 
                "MULTIPLEX = True on your server?" % (self.MODULE))
            self.processor = processors[0].processor
        else:
            # For multiplexed services, register all that match.
            self.processor = TMultiplexedProcessor()
            for processor_task in processors:
                self.logger.info("Registering %s as Multiplexed Service, '%s'",
                                 processor_task.processor,
                                 processor_task.service_name)
                self.processor.registerProcessor(processor_task.service_name,
                                                 processor_task.processor)

    def _checkTaskModule(self, task):
        """Returns True if `task` implements the appropriate MODULE Iface"""
        # Skip non-ThriftHandlerTasks
        if not isinstance(task, ThriftHandlerTask):
            return False

        # If self.MODULE is None, then connect *any* ThriftHandlerTask.
        if self.MODULE is None:
            return True

        # Otherwise, if this is the same thrift module as the handler, we have
        # a match
        if self.MODULE is task.MODULE:
            return True

        # If they did not match, there's a chance that we used in-process
        # thrift compilation to produce separate instances of equivalent
        # modules.  Check the individual methods on the handler to make sure
        # are sort of similar (though the args may differ...).
        # TODO: Consider re-evaluating this strategy longer-term.

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

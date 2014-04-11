# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""vservice defines the base service class, `VService`

VService can be used directly, for example with `VService.initFromCLI()`,
or it can be subclassed and used similarly.
"""
from __future__ import absolute_import
from __future__ import print_function

import logging
import signal
import sys
import threading
import time

from argparse import ArgumentParser
from .compat import OrderedDict

from .vtask import SkipTask, resolve_dependencies, get_registered_tasks
from .deps import HAS_PSUTIL
from .sparts import _SpartsObject, option


class VService(_SpartsObject):
    """Core class for implementing services."""
    DEFAULT_LOGLEVEL = 'DEBUG'
    REGISTER_SIGNAL_HANDLERS = True
    TASKS = []
    VERSION = ''
    _name = None
    dryrun = option(action='store_true', help='Run in "dryrun" mode')
    level = option(default=DEFAULT_LOGLEVEL, help='Log Level [%(default)s]')
    register_tasks = option(name='tasks', default=None,
                            metavar='TASK', nargs='*',
                            help='Tasks to run.  Pass without args to see the '
                                 'list. If not passed, all tasks will be '
                                 'started')
    if HAS_PSUTIL:
        runit_install = option(action='store_true',
                               help='Install this service under runit.')

    def __init__(self, ns):
        super(VService, self).__init__()
        self.logger = logging.getLogger(self.name)
        self.options = ns
        self.initLogging()
        self._stop = False
        self._restart = False
        self.tasks = []
        self.warnings = OrderedDict()
        self.warning_id = 0
        self.start_time = time.time()

    def initService(self):
        """Override this to do any service-specific initialization"""

    @classmethod
    def _resolveDependencies(cls):
        tasks = set(cls.TASKS).union(get_registered_tasks())
        return resolve_dependencies(tasks)

    @classmethod
    def _loptName(cls, name):
        return '--' + name.replace('_', '-')

    def preprocessOptions(self):
        """Processes "action" oriented options."""
        if self.getOption('runit_install'):
            self._install()

        if self.options.tasks == []:
            print("Available Tasks:")
            for t in self._resolveDependencies():
                print(" - %s" % t.__name__)
            sys.exit(1)

    def _createTasks(self):
        all_tasks = self._resolveDependencies()

        selected_tasks = self.options.tasks
        if selected_tasks is None:
            selected_tasks = [t.__name__ for t in all_tasks]

        for t in all_tasks:
            if t.__name__ in selected_tasks:
                self.tasks.append(t(self))

        # Call service initialization hook after tasks have been instantiated,
        # but before they've been initialized.
        self.initService()

        exceptions = []
        required = []
        for t in self.tasks:
            try:
                t.initTask()
                required.append(t)
            except SkipTask as e:
                self.logger.info("Skipping %s (%s)", t.name, e)
            except Exception as e:
                self.logger.exception("Error creating task, %s", t.name)
                exceptions.append(e)
        self.tasks = required

        if len(exceptions):
            raise Exception("Unable to start service (%d task start errors)" %
                            len(exceptions))

    def _handleShutdownSignals(self, signum, frame):
        assert signum in (signal.SIGINT, signal.SIGTERM)
        self.logger.info('signal -%d received', signum)
        self.shutdown()

    def _startTasks(self):
        if self.REGISTER_SIGNAL_HANDLERS:
            # Things seem to fail more gracefully if we trigger the stop
            # out of band (with a signal handler) instead of catching the
            # KeyboardInterrupt...
            signal.signal(signal.SIGINT, self._handleShutdownSignals)
            signal.signal(signal.SIGTERM, self._handleShutdownSignals)
        for t in self.tasks:
            t.start()
        self.logger.debug("All tasks started")

    def getTask(self, name):
        """Returns a task for the given class `name` or type, or None."""
        for t in self.tasks:
            if isinstance(name, str):
                if t.name == name:
                    return t
            else:
                if t.__class__ is name:
                    return t
        return None

    def requireTask(self, name):
        """Returns a task for the given class `name` or type, or throws."""
        t = self.getTask(name)
        if t is None:
            raise Exception("Task %s not found in service" % name)
        return t

    def shutdown(self):
        """Request a graceful shutdown.  Does not block."""
        self.logger.info("Received graceful shutdown request")
        self.stop()

    def restart(self):
        """Request a graceful restart.  Does not block."""
        self.logger.info("Received graceful restart request")
        self._restart = True
        self.stop()

    def stop(self):
        self._stop = True

    def _wait(self):
        try:
            self.logger.debug('VService Active.  Awaiting graceful shutdown.')

            # If there are no remaining tasks (or this service has no tasks)
            # just sleep until ^C is pressed
            while not self._stop:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info('KeyboardInterrupt Received!  Stopping Tasks...')

        for t in reversed(self.tasks):
            t.stop()

        try:
            self.logger.info('Waiting for tasks to shutdown gracefully...')
            for t in reversed(self.tasks):
                self.logger.debug('Waiting for %s to stop...', t)
                t.join()
        except KeyboardInterrupt:
            self.logger.warning('Abandon all hope ye who enter here')

    def join(self):
        """Blocks until a stop is requested, waits for all tasks to shutdown"""
        while not self._stop:
            time.sleep(0.1)
        for t in reversed(self.tasks):
            t.join()

    @classmethod
    def initFromCLI(cls, name=None):
        """Starts this service, processing command line arguments."""
        ap = cls._buildArgumentParser()
        ns = ap.parse_args()
        instance = cls.initFromOptions(ns, name=name)
        return instance

    @classmethod
    def initFromOptions(cls, ns, name=None):
        """Starts this service, arguments from `ns`"""
        instance = cls(ns)
        if name is not None:
            instance.name = name
        instance.preprocessOptions()
        return cls._runloop(instance)

    @classmethod
    def _runloop(cls, instance):
        while not instance._stop:
            try:
                instance._createTasks()
                instance._startTasks()
            except Exception:
                instance.logger.exception("Unexpected Exception during init")
                instance.shutdown()

            instance._wait()

            if instance._restart:
                instance = cls(instance.options)

        instance.logger.info("Instance shut down gracefully")

    def startBG(self):
        """Starts this service in the background

        Returns a thread that will join() on graceful shutdown."""
        self._createTasks()
        self._startTasks()
        t = threading.Thread(target=self._wait)
        t.start()
        return t

    @property
    def name(self):
        if self._name is None:
            self._name = self.__class__.__name__
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def initLogging(self):
        """Basic stderr logging.  Override this to do something else."""
        logging.basicConfig(level=self.loglevel, stream=sys.stderr)

    @classmethod
    def _makeArgumentParser(cls):
        """Create an argparse.ArgumentParser instance.

        Override this method if you already have an ArgumentParser instance to use
        or you simply want to specify some of the optional arguments to
        argparse.ArgumentParser.__init__
        (e.g. "fromfile_prefix_chars" or "conflict_handler"...)
        """
        return ArgumentParser()

    @classmethod
    def _buildArgumentParser(cls):
        ap = cls._makeArgumentParser()
        cls._addArguments(ap)

        all_tasks = set(cls.TASKS).union(get_registered_tasks())
        for t in resolve_dependencies(all_tasks):
            # TODO: Add each tasks' arguments to an argument group
            t._addArguments(ap)
        return ap

    @property
    def loglevel(self):
        # TODO: Deprecate this after proting args to proper option()s
        return getattr(logging, self.options.level)

    def getOption(self, name, default=None):
        return getattr(self.options, name, default)

    def setOption(self, name, value):
        setattr(self.options, name, value)

    def getOptions(self):
        return self.options.__dict__

    def _install(self):
        if not HAS_PSUTIL:
            raise NotImplementedError("You need psutil installed to install "
                                      "under runit")
        import sparts.runit
        sparts.runit.install(self.name)
        sys.exit(0)

    def getChildren(self):
        return dict((t.name, t) for t in self.tasks)

    def getWarnings(self):
        return self.warnings

    def registerWarning(self, message):
        wid = self.warning_id
        self.warning_id += 1
        self.warnings[wid] = message
        return wid

    def clearWarnings(self):
        self.warnings = OrderedDict()

    def clearWarning(self, id):
        if id not in self.warnings:
            return False
        del self.warnings[id]
        return True

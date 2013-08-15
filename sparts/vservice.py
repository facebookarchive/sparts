from __future__ import absolute_import
import logging
import sys
from argparse import ArgumentParser
from .vtask import SkipTask, resolve_dependencies, get_registered_tasks
import time
import threading
import signal
from .deps import HAS_PSUTIL
from .sparts import _SpartsObject


class VService(_SpartsObject):
    DEFAULT_LOGLEVEL = 'DEBUG'
    REGISTER_SIGNAL_HANDLERS = True
    TASKS = []
    VERSION = ''
    _name = None

    def __init__(self, ns):
        super(VService, self).__init__()
        self.logger = logging.getLogger(self.name)
        self.options = ns
        self.initLogging()
        self._stop = False
        self._restart = False
        self.tasks = []
        self.start_time = time.time()

    def createTasks(self):
        if self.getOption('runit_install'):
            self.install()

        all_tasks = set(self.TASKS).union(get_registered_tasks())
        all_tasks = resolve_dependencies(all_tasks)

        selected_tasks = self.options.tasks
        if selected_tasks == []:
            print "Available Tasks:"
            for t in all_tasks:
                print " - %s" % t.__name__
            sys.exit(1)

        if selected_tasks is None:
            selected_tasks = [t.__name__ for t in all_tasks]

        for t in all_tasks:
            if t.__name__ in selected_tasks:
                self.tasks.append(t(self))

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

    def handleShutdownSignals(self, signum, frame):
        assert signum in (signal.SIGINT, signal.SIGTERM)
        self.logger.info('signal -%d received', signum)
        self.shutdown()

    def startTasks(self):
        if self.REGISTER_SIGNAL_HANDLERS:
            # Things seem to fail more gracefully if we trigger the stop
            # out of band (with a signal handler) instead of catching the
            # KeyboardInterrupt...
            signal.signal(signal.SIGINT, self.handleShutdownSignals)
            signal.signal(signal.SIGTERM, self.handleShutdownSignals)
        for t in self.tasks:
            t.start()
        self.logger.debug("All tasks started")

    def getTask(self, name):
        for t in self.tasks:
            if isinstance(name, str):
                if t.name == name:
                    return t
            else:
                if t.__class__ is name:
                    return t
        return None

    def requireTask(self, name):
        t = self.getTask(name)
        if t is None:
            raise Exception("Task %s not found in service" % name)
        return t

    def shutdown(self):
        self.logger.info("Received graceful shutdown request")
        self.stop()

    def restart(self):
        self.logger.info("Received graceful restart request")
        self._restart = True
        self.stop()

    def stop(self):
        self._stop = True
        for t in reversed(self.tasks):
            t.stop()
            t.join()

    def join(self):
        self.logger.debug('VService Active.  Awaiting graceful shutdown.')
        try:
            for t in reversed(self.tasks):
                t.join()

            # If there are no remaining tasks (or this service has no tasks)
            # just sleep until ^C is pressed
            while not self._stop:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info('KeyboardInterrupt Received!  Stopping Tasks...')
            self.stop()
            for t in reversed(self.tasks):
                t.join()

    @classmethod
    def initFromCLI(cls, name=None):
        ap = cls._makeArgumentParser()
        ns = ap.parse_args()
        instance = cls.initFromOptions(ns, name=name)
        return instance

    @classmethod
    def initFromOptions(cls, ns, name=None):
        instance = cls(ns)
        if name is not None:
            instance.name = name
        return cls.runloop(instance)

    @classmethod
    def runloop(cls, instance):
        while not instance._stop:
            instance.createTasks()
            instance.startTasks()
            instance.join()

            if instance._restart:
                instance = cls(instance.options)

        instance.logger.info("Instance shut down gracefully")

    def startBG(self):
        self.createTasks()
        self.startTasks()
        t = threading.Thread(target=self.join)
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
        logging.basicConfig(level=self.loglevel, stream=sys.stderr)

    @classmethod
    def _makeArgumentParser(cls):
        ap = ArgumentParser()
        cls._addArguments(ap)

        all_tasks = set(cls.TASKS).union(get_registered_tasks())
        for t in resolve_dependencies(all_tasks):
            # TODO: Add each tasks' arguments to an argument group
            t._addArguments(ap)
        return ap

    @classmethod
    def _addArguments(cls, ap):
        # TODO: Use declarative options, like we do on tasks
        if HAS_PSUTIL:
            ap.add_argument('--runit-install', action='store_true',
                            help='Install this service under runit.')
        ap.add_argument('--tasks', default=None, nargs='*', metavar='TASK',
                        help='Tasks to run.  Pass without args to see the '
                             'list.  If not passed, all tasks will be started')
        ap.add_argument('--level', default=cls.DEFAULT_LOGLEVEL,
                        help='Log Level [%(default)s]')
        ap.add_argument('--dryrun', action='store_true',
                        help='Run in "dryrun" mode')
        return ap

    @property
    def loglevel(self):
        return getattr(logging, self.options.level)

    def getOption(self, name, default=None):
        return getattr(self.options, name, default)

    def setOption(self, name, value):
        setattr(self.options, name, value)

    def getOptions(self):
        return self.options.__dict__

    def install(self):
        if not HAS_PSUTIL:
            raise NotImplementedError("You need psutil installed to install "
                                      "under runit")
        import sparts.runit
        sparts.runit.install(self.name)
        sys.exit(0)

    def getChildren(self):
        return dict((t.name, t) for t in self.tasks)

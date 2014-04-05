"""Base Task and related helper classes for sparts' task system

Tasks in sparts are a way to organize and delegate some sort of
background or other synchronized processing.  This module defines
the most common features.
"""
import logging
import threading
from .sparts import _SpartsObject


_REGISTERED_TASKS = set()

class VTask(_SpartsObject):
    """The base class for all tasks.  Needs to be subclassed to be useful.

    Attributes:
        OPT_PREFIX - Overrides the prefix for any associated options
        LOOPLESS - True indicates this task should not spawn any threads
        DEPS - List of `VTask` subclasses that must be initialized first
        workers - Number of Threads that should execute the `_runloop`

    """

    OPT_PREFIX = None
    LOOPLESS = False
    DEPS = []
    workers = 1

    @property
    def name(self):
        return self.__class__.__name__

    def __init__(self, service):
        self.service = service
        self.logger = logging.getLogger('%s.%s' % (service.name, self.name))
        self.threads = []

    def initTask(self):
        """Override this to do any task-specific initialization

        Don't forget to call super(...).initTask(), or things may not
        run properly."""
        if not self.LOOPLESS:
            for i in xrange(self.workers):
                if self.workers == 1:
                    name = self.name
                else:
                    name = '%s-%d' % (self.name, i + 1)
                self.threads.append(
                    threading.Thread(target=self._run, name=name))

    def start(self):
        if not self.LOOPLESS:
            for thread in self.threads:
                thread.start()

    def stop(self):
        """Custom stopping logic for this task.

        This is called by the main VService thread, after a graceful shutdown
        request has been received."""
        pass

    def join(self):
        if not self.LOOPLESS:
            for thread in self.threads:
                while thread.isAlive():
                    thread.join(0.5)

    @property
    def running(self):
        """Returns True if task is still doing work.

        This base implementation returns True if any child threads are alive"""
        for thread in self.threads:
            if thread.isAlive():
                return True
        return False

    def _run(self):
        try:
            self._runloop()
        except Exception:
            # In general, you should not get here.  So, we will shutdown the
            # server.  It is better for your service to *completely* crash in
            # response to an unhandled error, than to continue on in some sort
            # of half-alive zombie state.  Please catch your exceptions.
            # Consider throwing a TryLater if this task is a subclass of
            # QueueTask or PeriodicTask.
            #
            # I hate zombies.
            self.logger.exception("Unhandled exception in %s", self.name)
            self.service.shutdown()
        finally:
            self.logger.debug('Thread %s exited',
                              threading.currentThread().name)

    def _runloop(self):
        """For normal (non-LOOPLESS) tasks, this MUST be implemented"""
        # TODO: May require some janky metaprogramming to make ABC enforce
        # this in a cleaner way.
        raise NotImplementedError()

    @classmethod
    def _loptName(self, *args):
        return '--' + self._optName(*args).replace('_', '-')

    @classmethod
    def _optName(cls, *args):
        name = cls.OPT_PREFIX or cls.__name__
        parts = [name]
        parts.extend((p.lower().replace('-', '_') for p in args))
        return '_'.join(parts)

    def getTaskOption(self, opt, default=None):
        return getattr(self.service.options,
                       self._optName(opt), default)

    @classmethod
    def _addArguments(cls, ap):
        for k in dir(cls):
            v = getattr(cls, k)
            regfunc = getattr(v, '_addToArgumentParser', None)
            if regfunc is not None:
                regfunc(cls, ap)

    @classmethod
    def register(cls):
        _REGISTERED_TASKS.add(cls)


def get_registered_tasks():
    return _REGISTERED_TASKS.copy()


class SkipTask(Exception):
    """Throw during initTask() to skip execution of this task.

    Useful in case the task is missing configuration critical to its operation,
    but not critical to the overall program.

    A good example might be a network-based logging task."""
    pass


class TryLater(Exception):
    """Throw this in overridden tasks to defer execution.

    Can be used to temporarily suspend and restart execution, which is useful
    for handling unexpected error conditions, or re-scheduling work."""
    pass


class ExecuteContext(object):
    """An abstraction used internally by various tasks to track work

    Encapsulates common metrics for work that can be retried later, hooks for
    signalling completion, etc"""
    def __init__(self, attempt=1, item=None, deferred=None):
        self.attempt = attempt
        self.item = item
        self.deferred = deferred


def resolve_dependencies(task_classes):
    """Returns a flattened dependency chain for `task_classes`.

    Turns a short list of `Task` subclasses into a longer list of `Task`
    subclasses.  This is useful for tasks that depend on other tasks, such as
    TwistedTask subclasses that must initialize and run after the Twisted
    reactor has been started."""
    result = []
    for t in task_classes:
        assert issubclass(t, VTask)
        for dep in resolve_dependencies(t.DEPS):
            if dep not in result:
                result.append(dep)

        if t not in result:
            result.append(t)
    return result

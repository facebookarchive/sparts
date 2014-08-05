# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Base Task and related helper classes for sparts' task system

Tasks in sparts are a way to organize and delegate some sort of
background or other synchronized processing.  This module defines
the most common features.
"""
from __future__ import absolute_import
import logging
import six
import threading

from six.moves import xrange
from sparts.sparts import _SpartsObject
from sparts.timer import Timer


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
        """Task Constructor.  requires a `service` VService instance

        You should not need to override this.  Override initTask isntead."""
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

    def initTaskThread(self):
        """Override thread-specific initialization for multi-threaded tasks"""

    def start(self):
        """Called during bootstrap to spin up threads post-creation."""
        if not self.LOOPLESS:
            for thread in self.threads:
                thread.start()

    def stop(self):
        """Custom stopping logic for this task.

        This is called by the main VService thread, after a graceful shutdown
        request has been received."""
        pass

    def join(self):
        """Block, waiting for all child worker threads to finish."""
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
            self.initTaskThread()
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
    def _loptName(cls, name):
        return '--' + cls._optName(name).replace('_', '-')

    @classmethod
    def _optName(cls, name):
        parts = [cls.OPT_PREFIX or cls.__name__, name]
        return '_'.join(parts).replace('-', '_')

    def getTaskOption(self, opt, default=None):
        return getattr(self.service.options,
                       self._optName(opt), default)

    def setTaskOption(self, opt, value):
        setattr(self.service.options, self._optName(opt), value)

    @classmethod
    def register(cls):
        REGISTERED.register(cls)


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
    def __init__(self, attempt=1, item=None, deferred=None, future=None):
        self.attempt = attempt
        self.item = item
        self.deferred = deferred
        self.future = future
        self.running = threading.Event()
        self.timer = Timer()

    def start(self):
        """Indicate that execution has started"""
        if not self.running.is_set():
            if self.future is not None:
                self.future.set_running_or_notify_cancel()
            self.timer.start()
            self.running.set()

    def set_result(self, result):
        """Indicate that execution has completed"""
        self.timer.stop()
        if self.future is not None:
            self.future.set_result(result)
        if self.deferred is not None:
            self.deferred.callback(result)

    def set_exception(self, exception):
        """Indicate that execution has failed"""
        handled = False

        self.timer.stop()
        if self.future is not None:
            self.future.set_exception(exception)

        if self.deferred is not None:
            unhandled = []
            self.deferred.addErrback(self._unhandledErrback, unhandled)
            self.deferred.errback(exception)
            if not unhandled:
                handled = True

        return handled

    @property
    def elapsed(self):
        """Convenience property.  Returns timer duration."""
        return self.timer.elapsed

    @staticmethod
    def _unhandledErrback(error, unhandled):
        """Fallback errback for deferred processing"""
        unhandled.append(error)
        return None

    def __cmp__(self, obj):
        """Custom comparators for comparing contexts' work `item`s"""
        lhs, rhs = id(self), obj
        if isinstance(obj, ExecuteContext):
            lhs, rhs = self.item, obj.item

        return cmp(lhs, rhs)

    def __lt__(self, obj):
        """Override __lt__ explicitly for priority queue implementations"""
        assert isinstance(obj, ExecuteContext)
        return self.item < obj.item

    def __eq__(self, obj):
        assert isinstance(obj, ExecuteContext)
        return self.item == obj.item

    def __ne__(self, obj):
        assert isinstance(obj, ExecuteContext)
        return self.item != obj.item

    def __gt__(self, obj):
        assert isinstance(obj, ExecuteContext)
        return self.item > obj.item

class Tasks(object):
    """Collection class for dealing with service tasks.

    Tasks can be accessed but accessing them (by name) as attributes, or via
    the get/require methods.
    """
    def __init__(self, tasks=None):
        self.logger = logging.getLogger('sparts.tasks')
        self._registered = []
        self._registered_names = {}
        self._created = []
        self._created_names = {}
        self._did_create = False

        tasks = tasks or []
        for t in tasks:
            self.register(t)

    def register(self, task_class):
        """Register task_class with the collection"""
        assert not self._did_create
        name = task_class.__name__
        if name not in self._registered_names:
            # Recursively register dependencies
            for dep in task_class.DEPS:
                self.register(dep)

            self._registered.append(task_class)
            self._registered_names[name] = task_class

    def register_all(self, tasks):
        """Register multiple `tasks` classes with the collection"""
        assert not self._did_create
        for task in tasks:
            self.register(task)

    def unregister(self, task_class):
        """Unregister `task_class` from the collection"""
        assert not self._did_create
        self._registered.remove(task_class)
        del(self._registered_names[task_class.__name__])

    def create(self, *args, **kwargs):
        """Create all registered tasks.

        TODO: Handle SkipTask?
        """
        assert not self._did_create
        for task_cls in self._registered:
            task = task_cls(*args, **kwargs)
            self._created.append(task)
            self._created_names[task_cls.__name__] = task

        self._did_create = True

    def remove(self, task):
        """Remove created `task` from the collection"""
        assert self._did_create
        self._created.remove(task)
        del(self._created_names[task.name])

    def init(self):
        """Initialize all created tasks.  Remove ones that throw SkipTask."""
        assert self._did_create
        exceptions = []
        skipped = []

        for t in self:
            try:
                t.initTask()
            except SkipTask as e:
                # Keep track of SkipTasks so we can remove it from this
                # task collection
                self.logger.info("Skipping %s (%s)", t.name, e)
                skipped.append(t)
            except Exception as e:
                # Log and track unhandled exceptions during init, so we can
                # fail later.
                self.logger.exception("Error creating task, %s", t.name)
                exceptions.append(e)

        # Remove any tasks that should be skipped
        for t in skipped:
            self.remove(t)

        # Reraise a new exception, if any exceptions were thrown in init
        if len(exceptions):
            raise Exception("Unable to start service (%d task start errors)" %
                            len(exceptions))

    def start(self):
        """Start all the tasks, creating worker threads, etc"""
        assert self._did_create
        for t in self.tasks:
            t.start()

    def get(self, task):
        """Returns the `task` or its class, if creation hasn't happened yet."""
        if isinstance(task, six.string_types):
            name = task
        else:
            assert issubclass(task, VTask)
            name = task.__name__

        if self._did_create:
            return self._created_names.get(name)
        else:
            return self._registered_names.get(name)

    def require(self, task):
        """Return the `task` instance or class, raising if not found."""
        result = self.get(task)
        if result is None:
            raise KeyError('%s not in tasks (%s|%s)' %
                           (task, self.task_classes, self.tasks))

        return result

    @property
    def task_classes(self):
        """Accessor for accessing a copy of registered task classes"""
        return self._registered[:]

    @property
    def tasks(self):
        """Accessor for accessing a registered or instantiated task classes

        Return value varies based on whether `create()` has been called."""
        if self._did_create:
            return self._created[:]
        else:
            return self.task_classes

    def __getattr__(self, name):
        """Helper for accessing tasks using their name as an attribute."""
        return self.require(name)

    def __iter__(self):
        """Iterates on created or registered tasks, as appropriate."""
        return iter(self.tasks)

    def __len__(self):
        """Returns the number of created or registered tasks, as appropriate"""
        return len(self.tasks)

    def __getitem__(self, index):
        """Returns the created or registered task at the specified `index`"""
        return self.tasks[index]


# This `Tasks` collection tracks globally registered tasks.
REGISTERED = Tasks()

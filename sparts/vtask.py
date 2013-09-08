import logging
import threading
from .sparts import _SpartsObject


_REGISTERED_TASKS = set()

class VTask(_SpartsObject):
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
        pass

    def join(self):
        if not self.LOOPLESS:
            for thread in self.threads:
                while thread.isAlive():
                    thread.join(0.5)

    @property
    def running(self):
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
    pass


class TryLater(Exception):
    pass


class ExecuteContext(object):
    def __init__(self, attempt=1, item=None, deferred=None):
        self.attempt = attempt
        self.item = item
        self.deferred = deferred


def resolve_dependencies(task_classes):
    result = []
    for t in task_classes:
        assert issubclass(t, VTask)
        for dep in resolve_dependencies(t.DEPS):
            if dep not in result:
                result.append(dep)

        if t not in result:
            result.append(t)
    return result

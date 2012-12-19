import logging
import threading


class VTask(object):
    OPT_PREFIX = None
    LOOPLESS = False
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

    def _run(self):
        try:
            self._runloop()
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


class SkipTask(Exception):
    pass


class TryLater(Exception):
    pass


class ExecuteContext(object):
    def __init__(self, attempt=1, item=None, deferred=None):
        self.attempt = attempt
        self.item = item
        self.deferred = deferred

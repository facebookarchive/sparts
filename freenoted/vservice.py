import logging
import sys
from argparse import ArgumentParser
from vtask import SkipTask

class VService(object):
    DEFAULT_LOGLEVEL = 'DEBUG'
    TASKS = []

    def __init__(self, ns):
        self.logger = logging.getLogger(self.name)
        self.options = ns
        self.initLogging()
        self._stop = False
        self._restart = False
        self.tasks = []

    def createTasks(self):
        tasks = self.options.tasks
        if tasks == []:
            print "Available Tasks:"
            for t in self.TASKS:
                print " - %s" % t.__name__
            sys.exit(1)
            
        elif tasks is None:
            tasks = [t.__name__ for t in self.TASKS]

        created = []
        for t in self.TASKS:
            if t.__name__ in tasks:
                created.append(t(self))

        exceptions = []
        for t in created:
            try:
                t.initTask()
                self.tasks.append(t)
            except SkipTask:
                pass
            except Exception as e:
                self.logger.exception("Error creating task, %s", t.name)
                exceptions.append(e)

        if len(exceptions):
            raise Exception("Unable to start service (%d task start errors)" %
                            len(exceptions))

    def startTasks(self):
        for t in self.tasks:
            t.start()

    def requireTask(self, name):
        for t in self.tasks:
            if t.name == name:
                return t
        raise Exception("Task %s not found in service" % name)

    def shutdown(self):
        self.logger.info("Received graceful shutdown request")
        self.stop()

    def reinitialize(self):
        self.logger.info("Received graceful restart request")
        self._restart = True
        self.stop()

    def stop(self):
        self._stop = True
        for t in self.tasks:
            t.stop()

    def join(self):
        try:
            for t in self.tasks:
                t.join()
        except KeyboardInterrupt:
            self.logger.info('KeyboardInterrupt Received!  Stopping Tasks...')
            self.stop()
            for t in self.tasks:
                t.join()

    @classmethod
    def initFromCLI(cls):
        ap = cls._makeArgumentParser()
        for t in cls.TASKS:
            t._addArguments(ap)
        ns = ap.parse_args()
        return cls.initFromOptions(ns)

    @classmethod
    def initFromOptions(cls, ns):
        instance = cls(ns)
        return cls.runloop(instance)

    @classmethod
    def runloop(cls, instance):
        while not instance._stop:
            instance.createTasks()
            instance.startTasks()
            instance.join()

            if instance._restart:
                instance = cls(instance.options)

    @property
    def name(self):
        return self.__class__.__name__

    @name.setter
    def name(self, value):
        pass

    def initLogging(self):
        logging.basicConfig(level=self.loglevel, stream=sys.stderr)

    @classmethod
    def _makeArgumentParser(cls):
        ap = ArgumentParser()
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

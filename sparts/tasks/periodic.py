from ..vtask import VTask
import time
from ..sparts import option
from threading import Event


class PeriodicTask(VTask):
    INTERVAL = None

    interval = option('interval', type=float, metavar='SECONDS',
                      default=lambda cls: cls.INTERVAL,
                      help='How often this task should run [%(default)s] (s)')

    def initTask(self):
        super(PeriodicTask, self).initTask()
        assert self.getTaskOption('interval') is not None
        self.stop_event = Event()

    def stop(self):
        self.stop_event.set()
        super(PeriodicTask, self).stop()

    def _runloop(self):
        while not self.service._stop:
            t0 = time.time()
            self.execute()
            to_sleep = (t0 + self.interval) - time.time()
            if to_sleep > 0:
                if self.stop_event.wait(to_sleep):
                    return
            else:
                #self.incrementCounter('n_slow_intervals')
                pass

    def execute(self, context=None):
        self.logger.debug('execute')

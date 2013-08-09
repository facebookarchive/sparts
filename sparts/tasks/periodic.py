from ..vtask import VTask
import time
from ..sparts import option, counter, samples, SampleType
from threading import Event


class PeriodicTask(VTask):
    INTERVAL = None

    execute_duration = samples(windows=[60, 240],
       types=[SampleType.AVG, SampleType.MAX, SampleType.MIN])
    n_iterations = counter()
    n_slow_iterations = counter()

    interval = option(type=float, metavar='SECONDS',
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
            self.n_iterations.increment()
            self.execute_duration.add(time.time() - t0)
            to_sleep = (t0 + self.interval) - time.time()
            if to_sleep > 0:
                if self.stop_event.wait(to_sleep):
                    return
            else:
                self.n_slow_iterations.increment()

    def execute(self, context=None):
        self.logger.debug('execute')

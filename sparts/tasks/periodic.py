from ..vtask import VTask
import time
from ..sparts import option


class PeriodicTask(VTask):
    INTERVAL = None

    interval = option('interval', type=float, metavar='SECONDS',
                      default=lambda cls: cls.INTERVAL,
                      help='How often this task should run [%(default)s] (s)')

    def initTask(self):
        super(PeriodicTask, self).initTask()
        assert self.getTaskOption('interval') is not None

    def _runloop(self):
        while not self.service._stop:
            end_time = time.time() + self.interval
            self.execute()

            while not self.service._stop:
                tn = time.time()
                to_sleep = end_time - tn
                if to_sleep <= 0:
                    break
                time.sleep(min(0.1, to_sleep))

    def execute(self, context=None):
        self.logger.debug('execute')

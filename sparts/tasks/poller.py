from .periodic import PeriodicTask
from threading import Event


class PollerTask(PeriodicTask):
    def initTask(self):
        self.current_value = None
        self.fetched = Event()
        super(PollerTask, self).initTask()

    def execute(self, context=None):
        new_value = self.fetch()
        if self.current_value != new_value:
            self.onValueChanged(self.current_value, new_value)
        self.current_value = new_value
        self.fetched.set()

    def onValueChanged(self, old_value, new_value):
        self.logger.debug('onValueChanged(%s, %s)', old_value, new_value)

    def fetch(self):
        self.logger.debug('fetch')
        return None

    def getValue(self, timeout=None):
        self.fetched.wait(timeout)
        return self.current_value

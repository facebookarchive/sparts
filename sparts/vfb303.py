from .fb303 import FacebookService
from .fb303.ttypes import fb_status



class VServiceFB303Processor(FacebookService.Processor):
    def __init__(self, service):
        FacebookService.Processor.__init__(self, self)
        self.service = service

    def getName(self):
        return self.service.name

    def getVersion(self):
        return str(self.service.VERSION)

    def getStatus(self):
        # TODO: DEAD?  STARTING?  STOPPED? 
        if self.service._stop:
            return fb_status.STOPPING
        for task in self.service.tasks:
            if not task.LOOPLESS:
                for thread in task.threads:
                    if not thread.isAlive():
                        return fb_status.WARNING
        return fb_status.ALIVE
    
    def getStatusDetails(self):
        if self.service._stop:
            return '%s is shutting down' % (self.getName())
        for task in self.service.tasks:
            if not task.LOOPLESS:
                for thread in task.threads:
                    if not thread.isAlive():
                        return '%s has dead threads!' % task.name
        return ''

    def getCounters(self):
        return {}

    def getCounter(self):
        return 0

    def setOption(self, name, value):
        if value == '__None__':
            value = None
        else:
            cur_value = getattr(self.service.options, name)
            if cur_value is not None:
                try:
                    value = cur_value.__class__(value)
                except Exception as e:
                    self.logger.debug('Unable to cast %s to %s (%s)', value,
                                      cur_value.__class__, e)
        self.service.setOption(name, value)

    def getOption(self, name):
        value = self.service.getOption(name)
        if value is None:
            value = '__None__'
        return value

    def getOptions(self):
        result = {}
        for k in self.service.getOptions():
            result[k] = self.getOption(k)
        return result

    def aliveSince(self):
        return self.service.start_time

    def reinitialize(self):
        self.service.restart()

    def shutdown(self):
        self.service.shutdown()

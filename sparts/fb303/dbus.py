# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import

import dbus.service
from .ttypes import fb_status

import datetime
import logging
import functools
import os


# TODO- move this somewhere else
def log_unhandled(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logging.getLogger('sparts.dbus.fb303') \
                .exception('Unhandled Exception in dbus method')
            raise
    return wrapped

class FB303DbusService(dbus.service.Object):
    def __init__(self, bus, handler, name=None):
        parts = ['', 'fb303']
        if name:
            parts.insert(1, name)
        path = '/'.join(parts)
        dbus.service.Object.__init__(self, bus, path)
        self.bus = bus
        self.handler = handler
        self.logger = logging.getLogger('sparts.fb303.dbus')

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='s')
    def getName(self):
        return self.handler.getName()

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='s')
    def getVersion(self):
        return self.handler.getVersion()

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='s')
    def getStatus(self):
        return fb_status._VALUES_TO_NAMES[self.handler.getStatus()]

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='s')
    def getStatusDetails(self):
        return self.handler.getStatusDetails()

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='a{sx}')
    def getCounters(self):
        return self.handler.getCounters()

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='s', out_signature='x')
    def getCounter(self, key):
        return self.handler.getCounter(key)

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='ss', out_signature='')
    def setOption(self, key, value):
        if value == '__None__':
            value = None
        return self.handler.setOption(key, value)

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='s', out_signature='s')
    def getOption(self, key):
        value = self.handler.getOption(key)
        if value is None:
            value = '__None__'
        return str(value)

    @log_unhandled
    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='a{ss}')
    def getOptions(self):
        result = {}
        for k in self.handler.getOptions().iterkeys():
            result[k] = self.getOption(k)
        return result

    @log_unhandled
    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='i', out_signature='s')
    def getCpuProfile(self, profileDurationInSec):
        logging.getLogger('sparts.dbus').debug('[%s] startProfile', os.getpid())
        return self.handler.getCpuProfile(profileDurationInSec)

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='x')
    def aliveSince(self):
        return self.handler.aliveSince()

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='')
    def reinitialize(self):
        return self.handler.reinitialize()

    @dbus.service.method(dbus_interface='com.facebook.fb303.Service',
                         in_signature='', out_signature='')
    def shutdown(self):
        return self.handler.shutdown()

    @dbus.service.method(dbus_interface='org.sparts.FB303Service',
                         in_signature='sv', out_signature='')
    def setOptionV(self, key, value):
        self.handler.setOption(key, str(value))


    @dbus.service.method(dbus_interface='org.sparts.FB303Service',
                         in_signature='', out_signature='s')
    def aliveSinceStr(self):
        return datetime.datetime.fromtimestamp(self.handler.aliveSince()) \
                .strftime('%Y-%m-%d %H:%M:%S')

# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
from __future__ import absolute_import

import imp

def HAS(module):
    try:
        return __import__(module)
    except ImportError:
        return None

HAS_PSUTIL = HAS('psutil')
HAS_THRIFT = HAS('thrift')
HAS_DAEMONIZE = HAS('daemonize')

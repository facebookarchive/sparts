# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
import imp

def HAS(module):
    try:
        file, pathname, description = imp.find_module(module)
        return imp.load_module(module, file, pathname, description)
    except ImportError:
        return None

HAS_PSUTIL = HAS('psutil')
HAS_THRIFT = HAS('thrift')

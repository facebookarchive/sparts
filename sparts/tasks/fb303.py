# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module related to implementing fb303 thrift handlers"""
from __future__ import absolute_import

from .thrift import ThriftProcessorTask
from ..vfb303 import VServiceFB303Processor


class FB303ProcessorTask(ThriftProcessorTask):
    PROCESSOR = VServiceFB303Processor

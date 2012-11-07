from __future__ import absolute_import

from .thrift import ThriftProcessorTask
from ..vfb303 import VServiceFB303Processor


class FB303ProcessorTask(ThriftProcessorTask):
    PROCESSOR = VServiceFB303Processor

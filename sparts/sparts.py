from collections import deque
from functools import partial
import time


class SampleType:
    """Pass an array of these in the `types` paremeter to `sample()`"""
    COUNT = 'count'
    SUM = 'sum'
    AVG = 'avg'
    AVERAGE = 'avg'
    MAX = 'max'
    MIN = 'min'


class _Nameable(object):
    """Base class for attribute classes with automatically set `name` attribute"""
    def __init__(self, name):
        super(_Nameable, self).__init__()
        self.name = name

    def _getNameForIdentifier(self, name):
        return name


class _Bindable(object):
    def __init__(self, *args, **kwargs):
        self._bound = {}
        super(_Bindable, self).__init__(*args, **kwargs)

    def __get__(self, instance, owner):
        if owner is None:
            return self

        if owner not in self._bound:
            self._bound[owner] = self._bind(owner)

        return self._bound[owner]

    def _bind(self, obj):
        raise NotImplementedError


class _BaseCounter(_Nameable, _Bindable):
    """Base type for counter-like things"""
    suffix = 'UNDEF'

    def __init__(self, name=None):
        super(_BaseCounter, self).__init__(name)
        self._initialize()

    def _bind(self, obj):
        return self.__class__(name=self.name)

    def _initialize(self):
        raise NotImplementedError()

    def getvalue(self):
        raise NotImplementedError()

    def add(self, value):
        raise NotImplementedError()

    def __call__(self):
        return self.getvalue()

    def __int__(self):
        return int(self.getvalue())

    def __float__(self):
        return float(self.getvalue())

    def __str__(self):
        v = self.getvalue()
        if v is None:
            return '__None__'
        return str(v)


class ValueCounter(_BaseCounter):
    """Base type for counter-like things that have a `._value`"""
    DEFAULT_VALUE = 0.0
    def _initialize(self, value=None):
        self._value = value or self.DEFAULT_VALUE

    def getvalue(self):
        return self._value


class Sum(ValueCounter):
    """A running total"""
    suffix = SampleType.SUM

    def add(self, value):
        self._value += value

    def increment(self):
        self.add(1.0)

    def incrementBy(self, value):
        self.add(value)

    def reset(self, value=0):
        self._value = value

counter = Sum

class Count(ValueCounter):
    """A running count"""
    suffix = SampleType.COUNT
    DEFAULT_VALUE = 0

    def add(self, value):
        self._value += 1

class Average(_BaseCounter):
    """A running average"""
    suffix = SampleType.AVERAGE

    def _initialize(self):
        self._total = 0.0
        self._count = 0

    def add(self, value):
        # TODO: Re-use sibling total/count counters if present
        # not sure how to do this sensibly
        self._total += value
        self._count += 1

    def getvalue(self):
        if self._count == 0:
            return None
        return self._total / self._count


class Max(ValueCounter):
    """A running maximum"""
    suffix = SampleType.MAX
    DEFAULT_VALUE = None

    def add(self, value):
        if self._value is None:
            self._value = value
        elif value > self._value:
            self._value = value


class Min(ValueCounter):
    """A running minimum"""
    suffix = SampleType.MIN
    DEFAULT_VALUE = None

    def add(self, value):
        if self._value is None:
            self._value = value
        elif value < self._value:
            self._value = value

    def getvalue(self):
        return self._value

# TODO: Percentiles!!


# Lookup for mapping SampleTypes to their respective classes
_SampleMethod = {
    SampleType.COUNT: Count,
    SampleType.SUM: Sum,
    SampleType.AVERAGE: Average,
    SampleType.MAX: Max,
    SampleType.MIN: Min,
}


class samples(_Nameable, _Bindable):
    """`samples` are used to generate series of counters dynamically
    
    This is so you can say, keep track of the average duration of some event for
    the last minute, hour, day, etc, and export these as 4 separate counters.
    """
    def __init__(self, types=None, windows=None, name=None):
        super(samples, self).__init__(name)
        self.types = types or [SampleType.AVERAGE]
        # minutely, hourly
        self.windows = sorted(windows or [60, 3600])
        self.max_window = max(self.windows)
        self.samples = deque()
        self.dirty = True
        self._prev_counters = {}
        self._prev_time = None

    def _bind(self, obj):
        return self.__class__(types=self.types, windows=self.windows,
                              name=self.name)

    def add(self, value):
        now = time.time()
        self.samples.append((now, value))

        # When adding samples, trim old ones.
        while now - self.max_window > self.samples[0][0]:
            self.samples.popleft()
        self.dirty = True

        # TODO: Handle "infinite" windows

    def getCounters(self):
        if self.dirty is False and self._prev_time == int(time.time()):
            return self._prev_counters

        ops = []
        for type in self.types:
            ops.append(_SampleMethod[type]())

        now = time.time()
        genwindows = iter(self.windows)
        window = genwindows.next()
        result = {}
        done = False

        def _saveCounterValues(window):
            """Re-usable helper function for setting results and continuing"""
            for op in ops:
                result[self.name + '.' + op.suffix + '.' + str(window)] = \
                    op.getvalue()
            # Move to the next window
            try:
                return genwindows.next(), False
            except StopIteration:
                # We exhausted all our windows
                return None, True

        for ts, value in reversed(self.samples):
            # We exceeded the current window
            if now - window > ts:
                # Save counter values
                window, done = _saveCounterValues(window)
                if done:
                    break

            for op in ops:
                op.add(value)

        # We exhausted the samples before the windows
        while not done:
            window, done = _saveCounterValues(window)

        self._prev_counters = result
        self._prev_time = int(now)
        self.dirty = False
        return result

    def getCounter(self, name, default=None):
        return self.getCounters().get(name, default)

    def iterkeys(self):
        for type in self.types:
            for window in self.windows:
                yield self.name + '.' + type + '.' + str(window)
        # TODO: Infinite Windows
            

class option(_Nameable):
    def __init__(self, name=None, type=None, default=None, help=None,
                 action=None, metavar=None, required=False, choices=None):
        super(option, self).__init__(name)

        # Set defaults for action=storeX to bool (otherwise, str)
        if type is None:
            if action in ['store_true', 'store_false']:
                type = bool
            else:
                type = str

        self.type = type
        self.default = default
        self.help = help
        self.action = action
        self.metavar = metavar
        self.required = required
        self.choices = choices

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        value = self._getter(obj)(self.name)
        if self.type is not None:
            value = self.type(value)
        return value

    def __set__(self, obj, value):
        if self.type is not None:
            value = self.type(value)
        self._setter(obj)(self.name, value)

    def _getter(self, obj):
        getter = getattr(obj, 'getTaskOption', None)
        if getter is None:
            getter = getattr(obj, 'getOption', None)
        assert getter is not None
        return getter

    def _setter(self, obj):
        setter = getattr(obj, 'setTaskOption', None)
        if setter is None:
            setter = getattr(obj, 'setOption', None)
        assert setter is not None
        return setter

    def _addToArgumentParser(self, task_cls, ap):
        name = task_cls._loptName(self.name)

        # This is kinda funky.  I want to support some form of shorthand
        # notation for overridable default values.  Doing it this way means we
        # can do option(..., default=lambda cls: cls.FOO, ...)
        default = self.default
        if callable(default):
            default = default(task_cls)

        kwargs = dict(default=default, help=self.help, action=self.action,
                      required=self.required)
        if self.action is None:
            kwargs['metavar'] = self.metavar
            kwargs['type'] = self.type
            kwargs['choices'] = self.choices
        ap.add_argument(name, **kwargs)

    def _getNameForIdentifier(self, name):
        return name.replace('_', '-')


class _NameHelper(type):
    def __new__(cls, name, bases, attrs):

        for k, v in attrs.iteritems():
            # Assign `name` for options
            if not isinstance(v, _Nameable):
                continue
            if v.name is not None:
                continue
            v.name = v._getNameForIdentifier(k)
        return super(_NameHelper, cls).__new__(cls, name, bases, attrs)


class _SpartsObject(object):
    __metaclass__ = _NameHelper

    def __new__(cls, *args, **kwargs):
        inst = super(_SpartsObject, cls).__new__(cls, *args, **kwargs)
        inst.counters = {}
        #for k, v in cls.__dict__.iteritems():
        for k in dir(cls):
            v = getattr(cls, k)
            if isinstance(v, _BaseCounter):
                inst.counters[v.name] = v
            elif isinstance(v, samples):
                for subcounter in v.iterkeys():
                    inst.counters[subcounter] = partial(
                        v.getCounter, subcounter)
        return inst

    def getCounters(self):
        result = {}
        for k in self.counters:
            result[k] = self.getCounter(k)

        for cn, c in self.getChildren().iteritems():
            for k in c.counters:
                result[cn + '.' + k] = c.getCounter(k)

        return result

    def getCounter(self, name):
        return self.counters.get(name, lambda: None)

    def getChildren(self):
        return {}

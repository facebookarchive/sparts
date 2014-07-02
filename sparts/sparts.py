# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module for common base classes and helpers, such as options and counters"""
from __future__ import absolute_import

from collections import namedtuple
from functools import partial
from six import iteritems


class _Nameable(object):
    """Base class for attribute classes with automatically set `name` attribute"""
    def __init__(self, name):
        super(_Nameable, self).__init__()
        self.name = name

    def _getNameForIdentifier(self, name):
        return name


class _Bindable(object):
    """Helper class for allowing instance-unique class-declarative behavior."""
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
        raise NotImplementedError()

class ProvidesCounters(object):
    def _genCounterCallbacks(self):
        """Yields this item's (names, value) counter tuple(s)."""
        raise NotImplementedError()

_AddArgArgs = namedtuple('_AddArgArgs', ['opts', 'kwargs'])

class option(_Nameable):
    def __init__(self, name=None, type=None, default=None, help=None,
                 action=None, metavar=None, required=False, choices=None,
                 nargs=None):
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
        self.nargs = nargs

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        value = self._getter(obj)(self.name)

        # If the default is of a different type than the option requires,
        # we should return the default.  Unfortunately, the way this is
        # currently implemented, it's impossible to detect this case.  For now,
        # let's treat `None` like a special case and return it as-is.
        if value is None:
            return value

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

    def _prepareForArgumentParser(self, task_cls):
        """Convert inst properties to *args, **kwargs for ap.add_argument().
        """
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
        if self.nargs is not None:
            kwargs['nargs'] = self.nargs
        return _AddArgArgs([name], kwargs)

    def _addToArgumentParser(self, optargs, ap):
        ap.add_argument(*optargs.opts, **optargs.kwargs)

    def _getNameForIdentifier(self, name):
        return name.replace('_', '-')


class _NameHelper(type):
    def __new__(cls, name, bases, attrs):

        for k, v in iteritems(attrs):
            # Assign `name` for options
            if not isinstance(v, _Nameable):
                continue
            if v.name is not None:
                continue
            v.name = v._getNameForIdentifier(k)
        return super(_NameHelper, cls).__new__(cls, name, bases, attrs)


_SpartsObjectBase = _NameHelper('_SpartsObjectBase', (object, ), {})

class _SpartsObject(_SpartsObjectBase):
    def __new__(cls, *args, **kwargs):
        inst = super(_SpartsObject, cls).__new__(cls)
        inst.counters = {}
        #for k, v in iteritems(cls.__dict__):

        # Traverse all child objects and statically assign a callable
        # reference to all child counters to the instance's counters dictionary.
        #
        # This is sort of implicitly broken for Callback counters, which are
        # defined after __new__ is called (e.g., during Task initialization)
        # TODO: Implement this in a better way.
        for k in dir(cls):
            v = getattr(cls, k)
            if isinstance(v, ProvidesCounters):
                for cn, cv in v._genCounterCallbacks():
                    inst.counters[cn] = cv

        return inst

    @classmethod
    def _loptName(cls, name):
        raise NotImplementedError()

    def getCounters(self):
        result = {}
        for k in self.counters:
            result[k] = self.getCounter(k)

        for cn, c in iteritems(self.getChildren()):
            for k in c.counters:
                result[cn + '.' + k] = c.getCounter(k)

        return result

    def getCounter(self, name):
        # Hack to get counters from a child task, even if the callable
        # wasn't statically assigned to this instance's counters dictionary.
        # TODO: Figure out a better way to do this.
        if name not in self.counters and '.' in name:
            child, sep, name = name.partition('.')
            return self.getChild(child).getCounter(name)

        return self.counters.get(name, lambda: None)

    def getChild(self, name):
        return self.getChildren()[name]

    def getChildren(self):
        return {}

    @classmethod
    def _addArguments(cls, ap):
        options = get_options(cls)
        for opt in options:
            opt.regfunc(ap)


_OptRegFunc = namedtuple('_OptRegFunc', ['opt', 'regfunc'])

def get_options(cls):
    """Get argparse options for class, `cls`

    Look for class level attributes of type option and
    convert them into the arguments  necessary for calling
    parser.add_argument().

    Arguments:
        subclass of VTask or Vservice - `cls`

    Returns:
        list(namedtuple) -
            .opt - namedtuple
                   .args - list of argument string names
                          (e.g. ['--help', '-h'])
                   .kwargs - dict of kwargs for add_argument()
                          (e.g. default=False, action='store_true' etc)
            .regfunc - callable that takes the ArgumentParser as an argument
                       and adds the option to it.
                       (e.g. "foo.regfunc(ap)" registers the foo option on ap)
    """
    ret = []
    for k in dir(cls):
        v = getattr(cls, k)
        preparefunc = getattr(v, '_prepareForArgumentParser', None)
        if not preparefunc:
            continue
        opt = preparefunc(cls)
        regfunc = partial(getattr(v, '_addToArgumentParser'), opt)
        ret.append(_OptRegFunc(opt, regfunc))
    return ret

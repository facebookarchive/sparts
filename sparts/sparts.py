

class option(object):
    def __init__(self, name, type=str, default=None, help=None,
                 action=None, metavar=None):
        self.name = name
        self.type = type
        self.default = default
        self.help = help
        self.action = action
        self.metavar = metavar

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

        kwargs = dict(default=default, help=self.help, action=self.action)
        if self.action is None:
            kwargs['metavar'] = self.metavar
            kwargs['type'] = self.type
        ap.add_argument(name, **kwargs)

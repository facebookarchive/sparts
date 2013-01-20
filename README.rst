There is a lot of boilerplate and copypasta associated with building
services (or any other software that runs continuously and does things)

sparts is a python library that aims to eliminate as much of the boiler
plate as possible, making it as dead simple to write new services with
little to no code.

Design Goals
============

-  Be able to implement services using sparts with as little code as
   possible
-  Support as many RPC transports as possible (thrift, http, dbus, etc)
-  Make it painless to integrate services that require custom IO loops
   (twisted, tornado, glib, etc)

HOWTO
=====

A sparts service typically consists of two parts, the "service"
definition, and its tasks.

Service
-------

``sparts.vtask.VService`` - This is the meat of any service implemented
on sparts.

Simply put, just subclass VService, and run initFromCLI() and you are
done.

For example, myservice.py:

::

    from sparts.vservice import VService
    class MyService(VService):
        pass

    MyService.initFromCLI()

Now, you can run this file with python -h (to see the available
options), or run with: ``python myservice.py``

This should emit something like the following output:

::

    DEBUG:VService:All tasks started``

And pressing ^C will emit:

::

    ^CINFO:VService:KeyboardInterrupt Received!  Stopping Tasks...
    INFO:VService:Instance shut down gracefully

This simple service, by itself, is pretty damn useless. That's where Tasks come into play

Tasks
-----

``sparts.vtask.VTask`` - This is the base class for all tasks

Tasks are what trigger your program to take action. This action can be
processing periodic events, handling HTTP requests, handling thrift
requests, working on items from a queue, waking up on an event,
operating some ioloop, or whatever.

Here's a simple example of a service with tasks (requires tornado
installed):

::

    from sparts.vservice import VService
    from sparts.tasks.tornado import TornadoIOLoopTask, TornadoHTTPTask

    class MyService(VService):
        ALL_TASKS=[TornadoIOLoopTask, TornadoHTTPTask]
        DEFAULT_PORT=8000

    MyService.initFromCLI()

Now running it emits:

::

    > python myservice.py --http-port 8000
    INFO:MyService.TornadoHTTPTask:TornadoHTTPTask Server Started on 0.0.0.0:8000
    DEBUG:MyService:All tasks started

And as you can see, you can curl the webserver:

::

    > curl localhost:8000
    Hello, world

HALP
====

If you have any questions, comments, feedback, suggestions, etc, please
feel free to contact me at any time at ruibalp@gmail.com or on
irc.freenode in ##sparts

There is a lot of boilerplate and copypasta associated with building
services (or any other software that runs continuously and does things)

sparts is a python library developed at Facebook that aims to eliminate
as much of the skeleton code as possible, making it as dead simple to
write new services with little to no excess code.

Design Goals
============

-  Be able to implement services with as little code as possible
-  Support as many RPC transports as possible (thrift, HTTP, dbus, etc)
-  Make it painless to integrate services that require custom IO loops
   (twisted, tornado, glib, etc)

HOWTO
=====

A sparts service typically consists of two parts, the core "service",
and its "tasks".  Background and offline processing are generally done
by tasks, while common or shared functionality belongs to the service.

Service
-------

``sparts.vtask.VService`` - This is the core of any sparts service.

Simply subclass VService for any custom service instance logic, and
run its initFromCLI() and you are done.

For example, myservice.py:

::

    from sparts.vservice import VService
    class MyService(VService):
        pass

    MyService.initFromCLI()

Now, you can run this file with the -h option (to see the available
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
    from sparts.tasks.tornado import TornadoHTTPTask
    TornadoHTTPTask.register()
    VService.initFromCLI()

Now running it emits:

::

    > python myservice.py --http-port 8000
    INFO:VService.TornadoHTTPTask:TornadoHTTPTask Server Started on 0.0.0.0 (port 8000)
    INFO:VService.TornadoHTTPTask:TornadoHTTPTask Server Started on :: (port 8000)
    DEBUG:MyService:All tasks started

And as you can see, you can curl the web server:

::

    > curl localhost:8000
    Hello, world

Tasks can be subclassed to do all kinds of things.  This one prints the current Unix
timestamp every second:

::

    from sparts.tasks.periodic import PeriodicTask

    class PrintClock(PeriodicTask):
        INTERVAL = 1.0
        def execute(self):
            print time.time()
    PrintClock.register()

    from sparts.vservice import VService
    VService.initFromCLI()

And the result:

::

    DEBUG:VService:All tasks started
    DEBUG:VService:VService Active.  Awaiting graceful shutdown.
    1376081805.08
    1376081806.08
    1376081807.08
    1376081808.08
    1376081809.08
    1376081810.08
    1376081811.08

HALP
====

If you have any questions, comments, feedback, suggestions, etc, please
feel free to contact me at any time.

-  email: ruibalp@gmail.com
-  twitter: http://twitter.com/fmoo
-  irc.freenode: #sparts
-  facebook: http://fb.me/ruibalp

License
=======
sparts is BSD-licensed.  We also provide an additional patent grant.

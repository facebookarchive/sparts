# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Tools for dynamically generating thrift code"""

import distutils.spawn
import imp
import os.path
import re
import subprocess

from sparts import ctx
from contextlib import contextmanager, nested


def compile(path, root='.', **kwargs):
    """Return a compiled thrift file module from `path`
    
    Additional kwargs may be passed to indicate options to the thrift compiler:

    - new_style [default:True]: Use new-style classes 
    - twisted [default:False]: Generated twisted-friendly bindings
    - tornado [default:False]: Generate tornado-friendly bindings
    - utf8strings [default:False]: Use unicode strings instead of native
    - slots [default:True]: Use __slots__ in generated structs
    """
    comp = _CompileContext(root=root)
    return comp.importThrift(path, **kwargs)


def _require_executable(name):
    """Given `name`, assert on and return the path to that binary."""
    path = distutils.spawn.find_executable(name)
    assert path is not None, 'Unable to find %s in PATH' % repr(name)
    return path


class _CompileContext(object):
    def __init__(self, root='.'):
        self.root = root
        self.thrift_bin = _require_executable('thrift')

    def getThriftOptions(self, new_style=True, twisted=False, tornado=False,
                         utf8strings=False, slots=True, dynamic=False,
                         dynbase=None, dynexc=None, dynimport=None):
        param = 'py'
        options = []
        if new_style:
            options.append('new_style')

        if twisted:
            options.append('twisted')
            assert not tornado

        if tornado:
            options.append('tornado')

        if utf8strings:
            options.append('utf8strings')

        if slots:
            options.append('slots')

        # TODO: Dynamic import jonx

        if len(options):
            param += ':' + ','.join(options)

        return param

    @contextmanager
    def _preCompileCtx(self, path, **kwargs):
        """Compiles a .thrift file and adds the output dir to the PYTHONPATH"""
        with ctx.tmpdir(prefix='tcomp') as tempdir:
            with ctx.add_path(tempdir):
                subprocess.check_output(
                    [self.thrift_bin, '-I', self.root, "--gen",
                     self.getThriftOptions(**kwargs),
                     '-v',
                     "-out", tempdir, os.path.join(self.root, path)])

                yield

    def importThrift(self, path, **kwargs):
        """Compiles a .thrift file, importing its contents into its return value"""
        path = os.path.abspath(path)

        with ctx.tmpdir(prefix='tcomp') as tempdir:
            output = subprocess.check_output(
                [self.thrift_bin, '-I', self.root, "--gen",
                 self.getThriftOptions(**kwargs),
                 '-v',
                 "-out", tempdir, os.path.join(self.root, path)])

            deps = []

            # Find dependencies and generate them in reversed order,
            # configuring context managers that will allow us to implicitly
            # add the generated code to our PYTHONPATH.
            for line in reversed(output.split('\n')):
                # When executing thrift with -v, explicit and implicit includes
                # are emitted to stdout in the following way:
                m = re.match('Scanning (.*) for includes', line)
                if m is None:
                    continue

                # Only pre-compile new dependencies
                if m.group(1) != path:
                    deps.append(self._preCompileCtx(m.group(1), **kwargs))

            result = None

            thriftname = os.path.splitext(os.path.basename(path))[0]
            with nested(*deps):
                for dirpath, dirnames, filenames in os.walk(tempdir):
                    # Emulate relative imports badly
                    with ctx.add_path(dirpath):
                        # Add types to module first
                        if 'ttypes.py' in filenames:
                            ttypes = self.importPython(dirpath + '/ttypes.py')
                            result = ttypes
                            filenames.remove('ttypes.py')

                        # Then constants
                        if 'constants.py' in filenames:
                            result = self.mergeModules(
                                self.importPython(dirpath + '/constants.py'),
                                result)
                            filenames.remove('constants.py')

                        for filename in filenames:
                            # Skip pyremotes
                            if not filename.endswith('.py') or \
                               filename == '__init__.py':
                                continue

                            # Attach services as attributes on the module.
                            svcpath = dirpath + '/' + filename
                            svcname = os.path.splitext(filename)[0]
                            svcmod = self.importPython(svcpath)
                            svcmod.__file__ = os.path.abspath(svcpath)
                            svcmod.__name__ = '%s.%s (generated)' % \
                                (thriftname, svcname)
                            setattr(result, svcname, svcmod)

            assert result is not None, "No files generated by %s" % (path, )

            # Set the __file__ attribute to the .thrift file instead
            # of the dynamically generated jonx
            result.__file__ = os.path.abspath(path)
            result.__name__ = thriftname + " (generated)"
            return result

    def mergeModules(self, module1, module2):
        if module1 is None:
            return module2

        if module2 is None:
            return module1

        for k in dir(module2):
            setattr(module1, k, getattr(module2, k))

        return module1

    def importPython(self, path):
        """Create a new module from code at `path`.

        Does not pollute python's module cache"""
        assert os.path.exists(path)

        # Any special variables we want to include in execution context
        orig_locals = {}
        exec_locals = orig_locals.copy()
        execfile(path, exec_locals, exec_locals)

        # Generate a new module object, and assign the modified locals
        # as attributes on it.
        result = imp.new_module(path)
        for k, v in exec_locals.iteritems():
            setattr(result, k, v)

        return result

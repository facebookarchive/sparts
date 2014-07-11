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
import tempfile

from six import iterkeys, iteritems
from sparts import ctx
from sparts.compat import OrderedDict, check_output
from sparts.fileutils import NamedTemporaryDirectory


def compile(path, root='.', debug=False, **kwargs):
    """Return a compiled thrift file module from `path`

    Additional kwargs may be passed to indicate options to the thrift compiler:

    - new_style [default:True]: Use new-style classes
    - twisted [default:False]: Generated twisted-friendly bindings
    - tornado [default:False]: Generate tornado-friendly bindings
    - utf8strings [default:False]: Use unicode strings instead of native
    - slots [default:True]: Use __slots__ in generated structs
    """
    comp = CompileContext(root=root, debug=debug)
    return comp.compileThriftFileAt(path, **kwargs)


def _require_executable(name):
    """Given `name`, assert on and return the path to that binary."""
    path = distutils.spawn.find_executable(name)
    assert path is not None, 'Unable to find %s in PATH' % repr(name)
    return path


class CompileContext(object):
    def __init__(self, root='.', debug=False):
        self.root = root
        self.thrift_bin = _require_executable('thrift')
        self.include_dirs = OrderedDict()
        self.dep_files = {}
        self.dep_contents = {}
        self.debug = debug

        self.addIncludeDir(self.root)

    def makeTemporaryIncludeDir(self):
        d = NamedTemporaryDirectory(prefix='tsrc_')
        if self.debug:
            d.keep()
        for k, v in iteritems(self.dep_contents):
            d.writefile(k, v)
        for k, v in iteritems(self.dep_files):
            d.symlink(k, v)
        return d

    def makeIncludeArgs(self, temp_include_dir=None):
        result = []
        for k in iterkeys(self.include_dirs):
            result += ['-I', k]

        if temp_include_dir is not None:
            result += ['-I', temp_include_dir.name]

        return result

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

    def addIncludeDir(self, path):
        assert os.path.exists(path) and os.path.isdir(path)
        self.include_dirs[os.path.abspath(path)] = True

    def addDependentFilePath(self, path):
        assert os.path.exists(path)

        self.dep_files[os.path.basename(path)] = os.path.abspath(path)

        path = os.path.dirname(path) or '.'
        self.addIncludeDir(path)

    def addDependentFileContents(self, name, contents):
        self.dep_contents[name] = contents

    def importThriftStr(self, payload, **kwargs):
        """Compiles a thrift file from string `payload`"""
        with tempfile.NamedTemporaryFile(suffix='.thrift') as f:
            if self.debug:
                f.delete = False
            f.write(payload)
            f.flush()
            return self.importThrift(f.name, **kwargs)

    def importThrift(self, path, **kwargs):
        """Compiles a .thrift file, importing its contents into its return value"""
        path = os.path.abspath(path)
        assert os.path.exists(path)
        assert os.path.isfile(path)

        srcdir = self.makeTemporaryIncludeDir()
        pathbase = os.path.basename(path)
        srcdir.symlink(pathbase, path)

        outdir = NamedTemporaryDirectory(prefix='to1_')
        outdir_recurse = NamedTemporaryDirectory(prefix='tor_')

        if self.debug:
            outdir.keep()
            outdir_recurse.keep()

        args = [self.thrift_bin] + self.makeIncludeArgs(srcdir) + \
               ["--gen", self.getThriftOptions(**kwargs), '-v',
                "-o", outdir.name, srcdir.join(pathbase)]
        check_output(args)

        args = [self.thrift_bin] + self.makeIncludeArgs(srcdir) + \
               ["--gen", self.getThriftOptions(**kwargs), '-v', '-r',
                "-o", outdir_recurse.name, srcdir.join(pathbase)]
        check_output(args)

        # Prepend output directory to the path
        with ctx.add_path(outdir_recurse.join('gen-py'), 0):

            thriftname = os.path.splitext(pathbase)[0]
            for dirpath, dirnames, filenames in os.walk(outdir.join('gen-py')):
                # Emulate relative imports badly
                dirpath = os.path.abspath(outdir.join('gen-py', dirpath))
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

        # Keep a copy of the module cache prior to execution
        with ctx.module_snapshot():
            execfile(path, exec_locals, exec_locals)

        # Generate a new module object, and assign the modified locals
        # as attributes on it.
        result = imp.new_module(path)
        for k, v in exec_locals.iteritems():
            setattr(result, k, v)

        return result

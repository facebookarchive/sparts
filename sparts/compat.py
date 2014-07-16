# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Run-time compatiblity helpers with third-party modules

For most standard library moves and discrepancies, you should use `six` instead
"""
from __future__ import absolute_import

try:
    from collections import OrderedDict
except ImportError:
    # Python2.6 compatibility
    from ordereddict import OrderedDict

try:
    from subprocess import check_output
except ImportError:
    import subprocess

    def check_output(args, stdin=None, stderr=None, shell=False,
                     universal_newlines=False):
        """Mostly compatible `check_output` for python2.6"""
        p = subprocess.Popen(args, stdin=stdin, stderr=stderr, shell=shell,
              universal_newlines=universal_newlines)
        output, stderr = p.communicate()
        returncode = p.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, cmd=args, output=output)
        return output

import logging
import sys

if sys.version >= '2.7':
    captureWarnings = logging.captureWarnings

else:
    import warnings

    # captureWarnings implementaiton copied from python-2.7.5
    _warnings_showwarning = None

    def _showwarning(message, category, filename, lineno, file=None, line=None):
        """
        Implementation of showwarnings which redirects to logging, which will first
        check to see if the file parameter is None. If a file is specified, it will
        delegate to the original warnings implementation of showwarning. Otherwise,
        it will call warnings.formatwarning and will log the resulting string to a
        warnings logger named "py.warnings" with level logging.WARNING.
        """
        if file is not None:
            if _warnings_showwarning is not None:
                _warnings_showwarning(message, category, filename, lineno, file, line)
        else:
            s = warnings.formatwarning(message, category, filename, lineno, line)
            logger = logging.getLogger("py.warnings")
            if not logger.handlers:
                logger.addHandler(logging.NullHandler())
            logger.warning("%s", s)

    def captureWarnings(capture):
        """
        If capture is true, redirect all warnings to the logging package.
        If capture is False, ensure that warnings are not redirected to logging
        but to their original destinations.
        """
        global _warnings_showwarning
        if capture:
            if _warnings_showwarning is None:
                _warnings_showwarning = warnings.showwarning
                warnings.showwarning = _showwarning
        else:
            if _warnings_showwarning is not None:
                warnings.showwarning = _warnings_showwarning
                _warnings_showwarning = None

    # TODO: urlparse that isn't broken for python2.6?

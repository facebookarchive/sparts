# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Run-time compatiblity helpers with third-party modules

For most standard library moves and discrepancies, you should use `six` instead
"""

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

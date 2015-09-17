# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import BaseSpartsTestCase, Skip
from sparts.thrift import compiler

# Only run thrift compiler test if the thrift compiler was found.
if compiler.get_executable() is None:
    raise Skip("Unable to find thrift binary on this system")


class ContextTests(BaseSpartsTestCase):
    def makeCompiler(self):
        return compiler.CompileContext()

    def testCompileFile(self):
        comp = self.makeCompiler()
        mod = comp.importThrift('thrift/fb303.thrift')
        self.assertTrue(hasattr(mod, 'FacebookService'))

    # Commented out until v1 of this is ready
    #def testCompileFileWithImplicitDeps(self):
    #    comp = self.makeCompiler()
    #    mod = comp.importThrift('thrift/sparts.thrift')
    #    self.assertTrue(hasattr(mod, 'SpartsService'))

    def testCompileServiceStr(self):
        comp = self.makeCompiler()
        mod = comp.importThriftStr("service FooService { }")
        self.assertTrue(hasattr(mod, 'FooService'))

    def testCompileStructStr(self):
        comp = self.makeCompiler()
        mod = comp.importThriftStr("struct FooStruct { }")
        self.assertTrue(hasattr(mod, 'FooStruct'))

    def testCompileDependentServiceStr(self):
        comp = self.makeCompiler()
        comp.addDependentFileContents("foo.thrift", "service FooService { }")
        mod = comp.importThriftStr("""
            include "foo.thrift"
            service BarService extends foo.FooService { }""")
        self.assertTrue(hasattr(mod, 'BarService'))

    def testCompileDependentStructStr(self):
        comp = self.makeCompiler()
        comp.addDependentFileContents("foo.thrift", "struct FooStruct { }")
        mod = comp.importThriftStr("""
            include "foo.thrift"
            struct BarStruct {
                1: foo.FooStruct fs;
            }""")
        self.assertTrue(hasattr(mod, 'BarStruct'))

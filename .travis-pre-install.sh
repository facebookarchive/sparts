#!/usr/bin/env bash

# Only prepare thrift stuff for python 2
if [ $(echo ${TRAVIS_PYTHON_VERSION} | cut -c1) = "2" ]; then

  # Prepare thrift for install
  pushd externals/thrift
  ./bootstrap.sh
  ./configure

  # Compile the thrift compiler
  echo "python " $(echo ${TRAVIS_PYTHON_VERSION} | cut -c1)
  pushd compiler/cpp
  make
  popd

  # Compiler the python extension/modules, etc
  pushd lib/py
  python setup.py build
  popd
  popd
fi

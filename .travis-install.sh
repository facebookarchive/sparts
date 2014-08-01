#!/usr/bin/env bash

# Only prepare thrift stuff for python 2
if [ $(echo ${TRAVIS_PYTHON_VERSION} | cut -c1) = "2" ]; then
# Install thrift-related dependencies
  pushd externals/thrift
  pushd compiler/cpp
  sudo make install
  popd
  pushd lib/py
  sudo python setup.py install
  popd
  popd
fi

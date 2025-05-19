#!/bin/bash

uv pip install --no-deps --target ./ pydoover
uv pip install --no-deps  --target ./ pydatamailbox

rm -rf ./pydoover/docker
rm -rf ./bin/
rm .lock

find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf

#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=".:$PYTHONPATH"
doover channel invoke-local-task --package-path . --profile staging --agent c026a1cb-6498-48be-918e-b2d3b645f6f1 on_fetch
#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
python3.11 -m pydoover deploy_config doover_config.json --profile staging --agent c026a1cb-6498-48be-918e-b2d3b645f6f1
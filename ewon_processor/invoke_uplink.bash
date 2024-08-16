#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
python3.11 -m pydoover invoke_local_task on_uplink . --profile staging --agent c026a1cb-6498-48be-918e-b2d3b645f6f1 --enable-traceback
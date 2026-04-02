from typing import Any

from pydoover.processor import run_app

from .application import DMApplication


def handler(event: dict[str, Any], context):
    run_app(DMApplication(), event, context)

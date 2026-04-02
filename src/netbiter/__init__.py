from typing import Any

from pydoover.processor import run_app

from .application import NetbiterApplication


def handler(event: dict[str, Any], context):
    run_app(NetbiterApplication(), event, context)

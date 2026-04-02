from typing import Any

from pydoover.processor import run_app

from .application import FTPApplication


def handler(event: dict[str, Any], context):
    run_app(FTPApplication(), event, context)

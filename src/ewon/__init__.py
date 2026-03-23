from typing import Any

from pydoover.processor import run_app

from .application import EwonApplication
from .app_config import EwonConfig


def handler(event: dict[str, Any], context):
    """
    Run the application.
    """
    # EwonConfig.clear_elements()
    run_app(EwonApplication(), event, context)

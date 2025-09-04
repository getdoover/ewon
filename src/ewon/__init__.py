from typing import Any

from pydoover.cloud.processor import run_app

from .application import EwonApplication
from .app_config import EwonConfig


def handler(event: dict[str, Any], context):
    """
    Run the application.
    """
    EwonConfig.clear_elements()
    run_app(EwonApplication(config=EwonConfig()), event, context)

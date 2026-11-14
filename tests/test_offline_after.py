"""The Offline After setting is on every processor's schema and defaults to 90 minutes."""

import importlib

import pytest

from ewon_common.application import DEFAULT_OFFLINE_AFTER

PROCESSORS = [("data_mailbox", "DMConfig"), ("netbiter", "NetbiterConfig"), ("ftp", "FTPConfig")]


@pytest.mark.parametrize("pkg, config_cls", PROCESSORS)
def test_every_processor_exposes_offline_after(pkg, config_cls):
    app_config = importlib.import_module(f"{pkg}.app_config")
    schema = getattr(app_config, config_cls).to_schema()
    prop = schema["properties"]["offline_after"]
    assert prop["default"] == DEFAULT_OFFLINE_AFTER == 90 * 60
    assert prop["minimum"] == 60
    assert prop["x-required"] is False

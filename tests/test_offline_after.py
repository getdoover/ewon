"""The Offline After setting is on every processor's schema and defaults to 90 minutes."""

import importlib
import inspect

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


APPS = [
    ("data_mailbox.application", "DMApplication"),
    ("netbiter.application", "NetbiterApplication"),
    ("ftp.application", "FTPApplication"),
]


@pytest.mark.parametrize("module, app_cls", APPS)
def test_handler_scan_before_config_load_does_not_raise(module, app_cls):
    # pydoover finds UI handlers with inspect.getmembers before it loads the
    # install's config. Anything on the app that reads config when looked up
    # raised there, and every invocation of every Ewon app died at setup.
    app = getattr(importlib.import_module(module), app_cls)()
    inspect.getmembers(app)
    assert app.offline_after_seconds() == DEFAULT_OFFLINE_AFTER


def test_offline_after_comes_from_the_config_once_loaded():
    from netbiter.application import NetbiterApplication

    app = NetbiterApplication()
    app.config._inject_deployment_config(
        {"offline_after": 14400, "tags": [], "exclude": [], "multiplots": [], "netbiter_system_id": "x", "netbiter_access_key": "x", "dv_proc_schedules": "rate(15 minutes)"}
    )
    assert app.offline_after_seconds() == 14400

"""Smoke tests: every processor in this repo imports and its config exports.

One repo, three lambda handlers (DataMailbox, Netbiter, FTP) sharing the
``ewon_common`` workspace package. These catch a broken import or a config
schema that no longer serialises before CI tries to publish.
"""

import pytest

APPS = [
    ("data_mailbox", "DMApplication", "DMConfig"),
    ("netbiter", "NetbiterApplication", "NetbiterConfig"),
    ("ftp", "FTPApplication", "FTPConfig"),
]


@pytest.mark.parametrize("package, app_cls, config_cls", APPS)
def test_import_handler(package, app_cls, config_cls):
    module = __import__(package)
    assert callable(module.handler)


@pytest.mark.parametrize("package, app_cls, config_cls", APPS)
def test_import_application(package, app_cls, config_cls):
    module = __import__(f"{package}.application", fromlist=[app_cls])
    app = getattr(module, app_cls)()
    assert app.config_cls.__name__ == config_cls
    # History must only ever be written at the frame timestamp, never by
    # pydoover's end-of-invocation flush at wall-clock time.
    assert app._record_tag_update is False


@pytest.mark.parametrize("package, app_cls, config_cls", APPS)
def test_config_exports(package, app_cls, config_cls):
    module = __import__(f"{package}.app_config", fromlist=[config_cls])
    config = getattr(module, config_cls)()
    schema = config.to_schema()
    assert isinstance(schema, dict)
    assert "UTC" in schema["properties"]["ewon_clock_timezone"]["enum"]


def test_import_clients():
    from data_mailbox.client import DataMailboxClient, Talk2MClient
    from ftp.client import FTPClient
    from netbiter.client import NetbiterAPIClient, NetbiterClient

    assert all((DataMailboxClient, Talk2MClient, FTPClient, NetbiterAPIClient, NetbiterClient))


def test_import_ewon_common():
    from ewon_common import (
        EwonBaseApplication,
        EwonCommonConfig,
        EwonTags,
        EwonUI,
        Tag,
        TagFrame,
        TagValue,
    )

    assert all((EwonBaseApplication, EwonCommonConfig, EwonTags, EwonUI, Tag, TagFrame, TagValue))

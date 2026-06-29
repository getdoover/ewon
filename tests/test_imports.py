import importlib

import pytest

# (package, application class, config class) for each processor in this repo.
PROCESSORS = [
    ("data_mailbox", "DMApplication", "DMConfig"),
    ("netbiter", "NetbiterApplication", "NetbiterConfig"),
    ("ftp", "FTPApplication", "FTPConfig"),
]


@pytest.mark.parametrize("pkg, app_cls, config_cls", PROCESSORS)
def test_processor_imports(pkg, app_cls, config_cls):
    # Lambda entry point - must import and expose a callable handler.
    root = importlib.import_module(pkg)
    assert callable(root.handler)

    # Application class.
    application = importlib.import_module(f"{pkg}.application")
    assert getattr(application, app_cls)

    # Config class generates a valid JSON schema (what `export` writes).
    app_config = importlib.import_module(f"{pkg}.app_config")
    schema = getattr(app_config, config_cls).to_schema()
    assert isinstance(schema, dict)


def test_shared_common_imports():
    from ewon_common.app_config import EwonCommonConfig
    from ewon_common.app_ui import EwonUI
    from ewon_common.application import EwonBaseApplication
    from ewon_common.tags import Tag, TagFrame, TagValue  # noqa: F401

    assert EwonCommonConfig
    assert EwonUI
    assert EwonBaseApplication
    assert Tag and TagValue and TagFrame

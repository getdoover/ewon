def test_import_application():
    from ewon.application import EwonApplication
    assert EwonApplication


def test_import_config():
    from ewon.app_config import EwonConfig
    config = EwonConfig()
    assert isinstance(config.to_dict(), dict)


def test_import_ui():
    from ewon.app_ui import EwonUI
    assert EwonUI


def test_import_handler():
    from ewon import handler
    assert callable(handler)


def test_import_ewon_client():
    from ewon.ewon_client import EwonClient, Talk2MClient
    assert EwonClient
    assert Talk2MClient


def test_import_tags():
    from ewon.tags import Tag, TagValue, TagFrame
    assert Tag
    assert TagValue
    assert TagFrame

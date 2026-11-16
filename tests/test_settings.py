"""The style choice is kept on disk."""
from vestigia import settings


def test_style_round_trip():
    store = settings.Store()
    assert store.load().style == "system"
    store.save(settings.Settings(style="dark"))
    assert settings.Store().load().style == "dark"

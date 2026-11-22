"""Tracking settings shared with the Dawarich account
(/api/v1/settings/mobile): the server's values win when it has any, a
new account gets the local ones. Off with `sync_with_server`."""
from phosh_toolkit import tasks

from vestigia.api import mobile_settings


def enabled(account, settings):
    return settings.sync_with_server and account.configured


def pull(account, store, done=None):
    """Fetch the server's settings into `store`; done(changed, error)."""
    settings = store.load()
    if not enabled(account, settings):
        if done:
            done(False, None)
        return
    client = account.client()

    def work():
        server = client.mobile_settings()
        if not server:
            client.update_mobile_settings(mobile_settings.to_server(settings))
            return False
        return mobile_settings.apply(server, settings)

    def finished(changed, error):
        if error is None and changed:
            store.save(settings)
        if done:
            done(bool(changed), error)

    tasks.run(work, finished)


def push(account, settings, done=None):
    if not enabled(account, settings):
        return
    tasks.run(account.client().update_mobile_settings,
              done or (lambda *_: None), mobile_settings.to_server(settings))

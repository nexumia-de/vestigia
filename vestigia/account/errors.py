"""Sentences for errors of server requests, for banners and toasts."""
from phosh_toolkit.http import HttpError

from vestigia.api.client import TOO_OLD


def describe(error):
    if isinstance(error, HttpError):
        if error.kind == "network":
            return ("The server cannot be reached. Check the address and the "
                    "network.")
        if error.kind == "auth" and str(error) == "Signed out by the server":
            return "The server rejected the API key"
        if error.kind == "server" and error.status == 404:
            return "No Dawarich server answers at this address"
        if error.kind in ("tls", TOO_OLD):
            return str(error)
        return str(error)
    return f"Something went wrong: {error}"

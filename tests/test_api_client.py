"""The Dawarich client against recorded answers of a real server."""
import pytest
from phosh_toolkit.http import AUTH, HttpError, Response

from vestigia.api import recorded, version
from vestigia.api.client import TOO_OLD, Dawarich, normalize_url

SERVER = "https://dawarich.example.org"


def client(key=recorded.KEY, **kwargs):
    return Dawarich(recorded.RecordedHttp(**kwargs), SERVER, key)


def test_versions():
    assert version.parse("1.18.1") == (1, 18, 1)
    assert version.parse("v1.22.0-rc1") == (1, 22, 0)
    assert version.supported("1.18.1") and version.supported("2.0")
    assert not version.supported("1.17.9") and not version.supported("")


def test_normalize_url():
    assert normalize_url(" dawarich.example.org/ ") == "https://dawarich.example.org"
    assert normalize_url("http://10.0.0.2:3000") == "http://10.0.0.2:3000"
    with pytest.raises(ValueError):
        normalize_url("")


def test_health_reads_the_version():
    assert client(key=None).health() == "1.18.1"


def test_old_server_is_refused():
    class Old:
        def request(self, *args, **kwargs):
            return Response(200, {"X-Dawarich-Version": "1.10.0"}, b'{"status":"ok"}')
    with pytest.raises(HttpError) as error:
        Dawarich(Old(), SERVER).health()
    assert error.value.kind == TOO_OLD and "1.18.1" in str(error.value)


def test_login_without_two_factor():
    login = client(key=None).login("demo@vestigia.test", recorded.PASSWORD)
    assert login.api_key == recorded.KEY and not login.challenge
    assert login.email == "demo@vestigia.test"


def test_wrong_password():
    with pytest.raises(HttpError) as error:
        client(key=None).login("demo@vestigia.test", "wrong")
    assert error.value.kind == AUTH and "password" in str(error.value)


def test_login_with_two_factor():
    c = client(key=None, two_factor=True)
    login = c.login("demo@vestigia.test", recorded.PASSWORD)
    assert login.challenge and not login.api_key
    with pytest.raises(HttpError):
        c.otp(login.challenge, "000000")
    assert c.otp(login.challenge, recorded.OTP).api_key == recorded.KEY


def test_key_only_in_the_header():
    c = client()
    assert c.me()["email"] == "demo@vestigia.test"
    for method, path, query, body in c.http.requests:
        assert recorded.KEY not in path and recorded.KEY not in str(query)


def test_rejected_key():
    with pytest.raises(HttpError) as error:
        client(key="not-the-key").me()
    assert error.value.kind == AUTH


def test_no_key_no_request():
    c = client(key="")
    with pytest.raises(HttpError):
        c.me()
    assert c.http.requests == []

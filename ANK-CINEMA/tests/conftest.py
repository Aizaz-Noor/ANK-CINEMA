"""pytest configuration and shared fixtures for ANK-Cinema tests."""

import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """
    Block all real network calls during testing.
    Any test that needs a network response must mock it explicitly.
    """
    import socket

    def _no_connect(*args, **kwargs):
        raise ConnectionError("Network access is disabled in tests. Use mock objects.")

    monkeypatch.setattr(socket, "getaddrinfo", _no_connect, raising=False)

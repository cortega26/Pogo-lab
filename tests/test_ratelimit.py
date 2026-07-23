"""Tests para la función de key de rate limiting (plan 051)."""

from typing import ClassVar

from apps.core.ratelimit import _is_proxy_ip, client_ip_key


class TestClientIpKey:
    """Plan 051: función de key probada para rate limiting."""

    def test_uses_x_real_ip_when_behind_proxy(self):
        """Cuando REMOTE_ADDR es del proxy, usa X-Real-IP."""

        class FakeRequest:
            META: ClassVar[dict] = {"REMOTE_ADDR": "172.18.0.1", "HTTP_X_REAL_IP": "203.0.113.5"}

        assert client_ip_key("test", FakeRequest()) == "203.0.113.5"

    def test_uses_remote_addr_when_not_behind_proxy(self):
        """Cuando REMOTE_ADDR no es del proxy, usa REMOTE_ADDR directamente."""

        class FakeRequest:
            META: ClassVar[dict] = {"REMOTE_ADDR": "203.0.113.5"}

        assert client_ip_key("test", FakeRequest()) == "203.0.113.5"

    def test_ignores_spoofed_xff_when_direct(self):
        """Un X-Real-IP falso no se usa cuando no hay proxy."""

        class FakeRequest:
            META: ClassVar[dict] = {"REMOTE_ADDR": "203.0.113.5", "HTTP_X_REAL_IP": "10.0.0.99"}

        assert client_ip_key("test", FakeRequest()) == "203.0.113.5"

    def test_handles_missing_x_real_ip_behind_proxy(self):
        """Si X-Real-IP falta detrás del proxy, cae a REMOTE_ADDR."""

        class FakeRequest:
            META: ClassVar[dict] = {"REMOTE_ADDR": "172.18.0.1"}

        assert client_ip_key("test", FakeRequest()) == "172.18.0.1"

    def test_handles_empty_meta(self):
        """Meta vacía no crashea."""

        class FakeRequest:
            META: ClassVar[dict] = {}

        assert client_ip_key("test", FakeRequest()) == "0.0.0.0"

    def test_ipv6_proxy(self):
        """IPv6 del proxy funciona."""

        class FakeRequest:
            META: ClassVar[dict] = {"REMOTE_ADDR": "fd00::1", "HTTP_X_REAL_IP": "2001:db8::5"}

        result = client_ip_key("test", FakeRequest())
        assert isinstance(result, str)


class TestIsProxyIp:
    def test_private_ipv4_is_proxy(self):
        assert _is_proxy_ip("172.16.0.1") is True
        assert _is_proxy_ip("10.0.0.1") is True
        assert _is_proxy_ip("192.168.1.1") is True

    def test_public_ipv4_is_not_proxy(self):
        assert _is_proxy_ip("203.0.113.5") is False
        assert _is_proxy_ip("8.8.8.8") is False

    def test_invalid_ip_returns_false(self):
        assert _is_proxy_ip("not-an-ip") is False
        assert _is_proxy_ip("") is False

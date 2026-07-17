"""Tests de rate limiting para login, registro y contribuciones."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import caches

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_rate_limit_cache(db):
    """Limpia la caché de rate limiting entre tests."""
    cache = caches["default"]
    cache.clear()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="test@example.com", password="testpass123")


@pytest.fixture
def ratelimit_on(settings):
    """Activa rate limiting para tests que lo necesitan."""
    settings.RATELIMIT_ENABLE = True


class TestLoginRateLimit:
    def test_under_limit_succeeds(self, client, user, ratelimit_on):
        url = "/es/cuenta/login/"
        for _ in range(5):
            response = client.post(url, {"login": user.email, "password": "testpass123"})
            assert response.status_code in (200, 302)

    def test_over_limit_returns_429(self, client, user, ratelimit_on):
        url = "/es/cuenta/login/"
        for i in range(5):
            response = client.post(url, {"login": user.email, "password": "testpass123"})
            assert response.status_code in (200, 302), f"Intento {i + 1}: {response.status_code}"
        response = client.post(url, {"login": user.email, "password": "testpass123"})
        assert response.status_code == 429

    def test_get_not_rate_limited(self, client, ratelimit_on):
        url = "/es/cuenta/login/"
        for _ in range(10):
            response = client.get(url)
            assert response.status_code == 200


class TestSignupRateLimit:
    def test_over_limit_returns_429(self, client, ratelimit_on):
        url = "/es/cuenta/signup/"
        for i in range(3):
            response = client.post(
                url,
                {
                    "email": f"user{i}@test.com",
                    "password1": "complexpass123",
                    "password2": "complexpass123",
                },
            )
            assert response.status_code in (200, 302), f"Intento {i + 1}: {response.status_code}"
        response = client.post(
            url,
            {
                "email": "blocked@test.com",
                "password1": "complexpass123",
                "password2": "complexpass123",
            },
        )
        assert response.status_code == 429


class TestContributionRateLimit:
    def test_over_limit_returns_429(self, client, user, ratelimit_on):
        client.force_login(user)
        url = "/es/contribuciones/consentir/"
        for i in range(10):
            response = client.post(url)
            assert response.status_code == 302, f"Intento {i + 1}: {response.status_code}"
        response = client.post(url)
        assert response.status_code == 429

    def test_different_user_independent_keys(self, client, user, ratelimit_on):
        """Cada usuario tiene su propio contador de rate limiting."""
        client.force_login(user)
        url = "/es/contribuciones/consentir/"
        for _ in range(10):
            response = client.post(url)
            assert response.status_code == 302
        response = client.post(url)
        assert response.status_code == 429


class TestRatelimitedErrorView:
    def test_429_page_content(self, client, user, ratelimit_on):
        url = "/es/cuenta/login/"
        for _ in range(5):
            client.post(url, {"login": user.email, "password": "testpass123"})
        response = client.post(url, {"login": user.email, "password": "testpass123"})
        assert response.status_code == 429
        content = response.content.decode()
        assert "429" in content
        assert "Demasiadas" in content or "solicitudes" in content.lower()

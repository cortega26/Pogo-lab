import pytest
from django.test import Client
from django.urls import resolve, reverse


class TestURLResolution:
    """Named URLs resolve correctly via reverse."""

    def test_account_login_resolves(self):
        url = reverse("account_login")
        assert url.startswith("/")
        assert "login" in url

    def test_account_logout_resolves(self):
        url = reverse("account_logout")
        assert url.startswith("/")

    def test_account_signup_resolves(self):
        url = reverse("account_signup")
        assert url.startswith("/")

    def test_account_export_resolves(self):
        url = reverse("account_export")
        assert url.startswith("/")
        assert "exportar" in url

    def test_account_delete_resolves(self):
        url = reverse("account_delete")
        assert url.startswith("/")
        assert "eliminar" in url

    def test_admin_resolves(self):
        url = reverse("admin:index")
        assert url.startswith("/")

    def test_set_language_resolves(self):
        view_func = resolve("/i18n/setlang/").func
        assert view_func.__name__ == "set_language"

    def test_set_language_reverse(self):
        url = reverse("set_language")
        assert url == "/i18n/setlang/"


class TestHealthz:
    """Health endpoint returns correct response."""

    def test_healthz_200_at_root(self):
        response = Client().get("/es/")
        assert response.status_code == 200

    def test_healthz_200_english(self):
        response = Client().get("/en/")
        assert response.status_code == 200

    def test_healthz_base_template(self):
        response = Client().get("/es/")
        html = response.content.decode().lower()
        assert "pogo-lab" in html


class TestI18n:
    """i18n_patterns work for all configured languages."""

    def test_spanish_prefix(self):
        response = Client().get("/es/")
        assert response.status_code == 200

    def test_english_prefix(self):
        response = Client().get("/en/")
        assert response.status_code == 200

    def test_i18n_patterns_404_for_unsupported_language(self):
        response = Client().get("/fr/")
        assert response.status_code == 404

    def test_set_language_endpoint(self):
        response = Client().post("/i18n/setlang/", {"language": "en"})
        assert response.status_code in (200, 302)

    def test_default_redirect_es(self):
        """Root URL (/) redirects to /es/ when prefix_default_language=True."""
        response = Client().get("/", follow=True)
        assert response.status_code == 200

    def test_404_for_unknown_path(self):
        response = Client().get("/es/no-existe/")
        assert response.status_code == 404

    def test_404_for_unknown_path_en(self):
        response = Client().get("/en/no-existe/")
        assert response.status_code == 404


class TestMiddlewares:
    """Core middlewares function correctly."""

    def test_correlation_id_in_response(self):
        response = Client().get("/es/")
        assert "X-Correlation-ID" in response.headers

    def test_correlation_id_is_uuid(self):
        response = Client().get("/es/")
        cid = response["X-Correlation-ID"]
        assert len(cid) == 36
        assert cid.count("-") == 4


@pytest.mark.django_db
class TestAuthSmoke:
    """Auth endpoints render correctly."""

    def test_login_page_200(self):
        response = Client().get("/es/cuenta/login/")
        assert response.status_code == 200

    def test_signup_page_200(self):
        response = Client().get("/es/cuenta/signup/")
        assert response.status_code == 200

    def test_export_page_redirects_when_anon(self):
        response = Client().get("/es/cuenta/exportar/")
        assert response.status_code == 302

    def test_delete_page_redirects_when_anon(self):
        response = Client().get("/es/cuenta/eliminar/")
        assert response.status_code == 302

    def test_export_page_en_redirects_when_anon(self):
        response = Client().get("/en/cuenta/exportar/")
        assert response.status_code == 302

    def test_delete_page_en_redirects_when_anon(self):
        response = Client().get("/en/cuenta/eliminar/")
        assert response.status_code == 302

    def test_export_page_200_when_logged_in(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(username="export_tester", password="pass1234")
        client = Client()
        client.force_login(user)
        response = client.get("/es/cuenta/exportar/")
        assert response.status_code == 200

    def test_delete_page_200_when_logged_in(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(username="delete_tester", password="pass1234")
        client = Client()
        client.force_login(user)
        response = client.get("/es/cuenta/eliminar/")
        assert response.status_code == 200

    def test_logout_on_get(self):
        """Logout page GET redirects (default allauth behaviour)."""
        response = Client().get("/es/cuenta/logout/")
        assert response.status_code in (200, 302)


class TestAdmin:
    """Admin interface accessible."""

    def test_admin_login_redirect(self):
        response = Client().get("/admin/")
        assert response.status_code == 302


class TestCoreModels:
    """TimestampedModel works."""

    def test_timestamped_model_importable(self):
        from apps.core.models import TimestampedModel

        assert TimestampedModel is not None
        assert hasattr(TimestampedModel, "created_at")
        assert hasattr(TimestampedModel, "updated_at")

    def test_healthz_view_name(self):
        from apps.core.views import healthz

        assert healthz is not None


@pytest.mark.django_db
class TestUserProfile:
    """UserProfile model and signal work."""

    def test_userprofile_created_on_user_creation(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="smoketest", email="test@example.com", password="pass1234"
        )
        assert hasattr(user, "profile")
        assert user.profile.locale == "es"

    def test_userprofile_defaults(self):
        from apps.accounts.models import UserProfile

        assert UserProfile._meta.get_field("locale").default == "es"
        assert UserProfile._meta.get_field("country").default == ""
        assert not UserProfile._meta.get_field("default_contribution_optin").default
        assert UserProfile._meta.get_field("display_prefs").default is dict

    def test_userprofile_verbose_name(self):
        from apps.accounts.models import UserProfile

        assert UserProfile._meta.verbose_name == "perfil de usuario"
        assert UserProfile._meta.verbose_name_plural == "perfiles de usuario"

    def test_userprofile_delete_cascades(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        from apps.accounts.models import UserProfile

        user = user_model.objects.create_user(
            username="delete_test", email="delete@example.com", password="pass1234"
        )
        profile_id = user.profile.id
        user.delete()
        assert not UserProfile.objects.filter(id=profile_id).exists()

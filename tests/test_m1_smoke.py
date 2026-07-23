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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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
        from django.urls import reverse
        from django.utils import translation

        with translation.override("en"):
            url = reverse("account_export")
        response = Client().get(url)
        assert response.status_code == 302

    def test_delete_page_en_redirects_when_anon(self):
        from django.urls import reverse
        from django.utils import translation

        with translation.override("en"):
            url = reverse("account_delete")
        response = Client().get(url)
        assert response.status_code == 302

    def test_export_page_200_when_logged_in(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            email="export_tester@example.com", password="pass1234"
        )
        client = Client()
        client.force_login(user)
        response = client.get("/es/cuenta/exportar/")
        assert response.status_code == 200

    def test_delete_page_200_when_logged_in(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            email="delete_tester@example.com", password="pass1234"
        )
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
        user = user_model.objects.create_user(email="test@example.com", password="pass1234")
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

        user = user_model.objects.create_user(email="delete@example.com", password="pass1234")
        profile_id = user.profile.id
        user.delete()
        assert not UserProfile.objects.filter(id=profile_id).exists()


@pytest.mark.django_db
class TestLegalViews:
    """Legal pages (ToS, privacy, disclaimer) render correctly."""

    def test_disclaimer_200(self):
        response = Client().get("/es/aviso-legal/")
        assert response.status_code == 200

    def test_disclaimer_200_en(self):
        response = Client().get("/en/aviso-legal/")
        assert response.status_code == 200

    def test_disclaimer_contains_no_affiliation(self):
        response = Client().get("/es/aviso-legal/")
        html = response.content.decode()
        assert "no está afiliado" in html
        assert "Niantic" in html

    def test_disclaimer_contains_no_affiliation_en(self):
        response = Client().get("/en/aviso-legal/")
        html = response.content.decode()
        assert "not affiliated" in html or "no está afiliado" in html
        assert "Niantic" in html

    def test_privacy_200(self):
        response = Client().get("/es/privacidad/")
        assert response.status_code == 200

    def test_privacy_200_en(self):
        response = Client().get("/en/privacidad/")
        assert response.status_code == 200

    def test_privacy_contains_key_content(self):
        response = Client().get("/es/privacidad/")
        html = response.content.decode()
        assert "recopilamos" in html.lower()

    def test_tos_200(self):
        response = Client().get("/es/terminos/")
        assert response.status_code == 200

    def test_tos_200_en(self):
        response = Client().get("/en/terminos/")
        assert response.status_code == 200

    def test_tos_contains_key_content(self):
        response = Client().get("/es/terminos/")
        html = response.content.decode()
        assert "términos" in html.lower() or "Términos" in html

    def test_healthcheck_json_no_i18n(self):
        """healthcheck.json is accessible without locale prefix for monitoring."""
        response = Client().get("/healthcheck.json")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"


class TestNewCalculatorsSmoke:
    """M8: las 5 nuevas calculadoras renderizan (GET) y calculan (POST)."""

    def test_cp_calculator_get(self):
        response = Client().get("/es/calculadora/cp/")
        assert response.status_code == 200

    def test_cp_calculator_post(self):
        response = Client().post(
            "/es/calculadora/cp/",
            {
                "species": "pikachu",
                "level": "20.0",
                "iv_atk": "10",
                "iv_def": "10",
                "iv_stam": "10",
            },
        )
        assert response.status_code == 200
        assert "CP" in response.content.decode() or "Resultados" in response.content.decode()

    def test_cp_calculator_post_htmx(self):
        response = Client().post(
            "/es/calculadora/cp/",
            {
                "species": "pikachu",
                "level": "20.0",
                "iv_atk": "10",
                "iv_def": "10",
                "iv_stam": "10",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200

    def test_cost_calculator_get(self):
        response = Client().get("/es/calculadora/costos/")
        assert response.status_code == 200

    def test_cost_calculator_post(self):
        response = Client().post(
            "/es/calculadora/costos/",
            {"from_level": "20.0", "to_level": "40.0"},
        )
        assert response.status_code == 200
        assert "225000" in response.content.decode()

    def test_pvp_ranker_get(self):
        response = Client().get("/es/calculadora/pvp/")
        assert response.status_code == 200

    def test_pvp_ranker_post(self):
        response = Client().post(
            "/es/calculadora/pvp/",
            {"species": "medicham", "league": "1500"},
        )
        assert response.status_code == 200
        # should contain a ranking table
        content = response.content.decode()
        assert "Rank" in content or "Stat Product" in content or "15" in content

    def test_catch_calculator_get(self):
        response = Client().get("/es/calculadora/captura/")
        assert response.status_code == 200

    def test_catch_calculator_post(self):
        response = Client().post(
            "/es/calculadora/captura/",
            {
                "species": "charmander",
                "level": "15.0",
                "ball": "1.0",
                "berry": "1.5",
                "curveball": "1",
                "throw": "1.15",
                "medal": "1.3",
            },
        )
        assert response.status_code == 200
        assert "%" in response.content.decode()

    def test_type_calculator_get(self):
        response = Client().get("/es/calculadora/tipos/")
        assert response.status_code == 200

    def test_type_calculator_post(self):
        response = Client().post(
            "/es/calculadora/tipos/",
            {"def_type1": "dragon", "def_type2": "flying"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "ice" in content.lower() or "fairy" in content.lower()

    def test_shiny_calculator_get(self):
        response = Client().get("/es/calculadora/shiny/")
        assert response.status_code == 200

    def test_shiny_calculator_post(self):
        response = Client().post(
            "/es/calculadora/shiny/",
            {"rate": "0.008", "n": "100", "confidence": "0.95"},
        )
        assert response.status_code == 200
        assert "%" in response.content.decode()

    def test_shadow_calculator_get(self):
        response = Client().get("/es/calculadora/shadow/")
        assert response.status_code == 200

    def test_shadow_calculator_post(self):
        response = Client().post(
            "/es/calculadora/shadow/",
            {
                "species": "machamp",
                "level": "40.0",
                "iv_atk": "15",
                "iv_def": "15",
                "iv_stam": "15",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "Purified" in content or "Shadow" in content or "Ataque" in content

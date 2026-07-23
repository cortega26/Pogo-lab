"""Tests de AuditEvent inmutable (plan 061)."""

import pytest


@pytest.mark.django_db
class TestAuditEventAdminReadonly:
    """Plan 061: el admin de AuditEvent es completamente readonly."""

    def test_admin_has_no_add_permission(self, admin_client):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        assert admin.has_add_permission(None) is False

    def test_admin_has_no_change_permission(self):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        assert admin.has_change_permission(None) is False

    def test_admin_has_no_delete_permission(self):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        assert admin.has_delete_permission(None) is False

    def test_all_fields_are_readonly(self):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        # Todos los campos deben estar en readonly_fields
        readonly = set(admin.readonly_fields)
        expected = {
            "verb",
            "actor",
            "target_type",
            "target_id",
            "metadata",
            "created_at",
            "correlation_id",
        }
        assert expected.issubset(readonly), f"Faltan campos readonly: {expected - readonly}"

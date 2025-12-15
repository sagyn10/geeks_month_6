import os
import django

os.environ. setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()
pytest_plugins = ['pytest_django']
# users/tests.py
from datetime import timedelta
import pytest
from django.core import mail
from django.utils import timezone
from django. conf import settings
from django.contrib.auth import get_user_model

# Импортируем задачи
from . tasks import (
    generate_users_report_task,
    deactivate_inactive_users_task,
    send_admin_stats_task
)


def test_generate_users_report_task(db):
    User = get_user_model()
    
    User.objects.create(email="test1@test.com")
    User.objects.create(email="test2@test. com")

    result = generate_users_report_task.apply()
    file_path = result. get()

    assert os.path.exists(file_path)


def test_deactivate_inactive_users_task(db):
    User = get_user_model()
    
    old_user = User.objects.create(
        email="old@test.com",
        is_active=True,
        last_login=timezone.now() - timedelta(days=40),
    )

    count = deactivate_inactive_users_task.apply().get()

    old_user.refresh_from_db()

    assert count == 1
    assert old_user.is_active is False


def test_send_admin_stats_task(db, settings):
    User = get_user_model()
    
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.ADMIN_EMAIL = "admin@test.com"

    User.objects.create(email="u1@test.com", is_active=True)
    User.objects.create(email="u2@test.com", is_active=False)

    result = send_admin_stats_task.apply().get()

    assert result is True
    assert len(mail. outbox) == 1
    assert "Всего пользователей" in mail.outbox[0]. body
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model  # ✅ ИЗМЕНЕНО
import json
from datetime import datetime, timedelta
import os
import csv
from pathlib import Path
from django.utils import timezone


@shared_task
def generate_user_statistics_report(user_id):
    """Генерирует файл со статистикой пользователя"""
    User = get_user_model()
    user = User.objects.get(id=user_id)
    
    # ✅ Безопасное получение атрибутов
    stats = {
        'user_id': user.id,
        'username': getattr(user, 'username', None),
        'email': getattr(user, 'email', None),
        'date_joined': str(getattr(user, 'date_joined', 'N/A')),
        'last_login': str(getattr(user, 'last_login', 'N/A')),
        'is_active': getattr(user, 'is_active', False),
        'total_posts': user.posts.count() if hasattr(user, 'posts') else 0,
        'generated_at': str(datetime.now())
    }
    
    # Создаем папку если нет
    os.makedirs('reports', exist_ok=True)
    
    filename = f'reports/user_{user_id}_stats.json'
    with open(filename, 'w') as f:
        json.dump(stats, f, indent=4)
    
    print(f"✅ Отчет сохранен:  {filename}")
    return filename


@shared_task
def cleanup_old_temp_files():
    """Удаляет временные файлы старше 7 дней"""
    temp_dir = 'media/temp/'
    
    # ✅ ДОБАВЛЕНА ПРОВЕРКА
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
        print(f"📁 Создана папка: {temp_dir}")
        return 0
    
    threshold_date = datetime.now() - timedelta(days=7)
    deleted_count = 0
    
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        
        if not os.path.isfile(filepath):  # ✅ ДОБАВЛЕНА ПРОВЕРКА
            continue
        
        file_time = datetime.fromtimestamp(os.path.getctime(filepath))
        
        if file_time < threshold_date: 
            os.remove(filepath)
            deleted_count += 1
            print(f"🗑️ Удален: {filename}")
    
    print(f"✅ Очистка завершена. Удалено файлов: {deleted_count}")
    return deleted_count


@shared_task
def notify_admin_about_error(error_type, details):
    """Отправляет email администратору при критических ошибках"""
    subject = f"⚠️ Критическая ошибка:  {error_type}"
    
    message = f"""
    Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Тип ошибки: {error_type}
    
    Детали: 
    {details}
    
    ---
    Это автоматическое уведомление системы мониторинга.
    """
    
    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', None) or settings.EMAIL_HOST_USER
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [admin_email],
            fail_silently=False,
        )
    except Exception as exc:
        print(f"notify_admin_about_error send_mail failed: {exc}")
        return f"error: {exc}"

    print(f"📧 Уведомление отправлено администратору о:  {error_type}")
    return "Email sent"


@shared_task
def send_otp_mail(email, code):
    """Отправка OTP кода"""
    print("#" * 20)
    try:
        send_mail(
            "Для подтверждения",
            f"Не сообщайте чужим людям: {code}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
    except Exception as exc:
        print(f"send_otp_mail send_mail failed: {exc}")
        return f"error: {exc}"
    return "Ok"


@shared_task
def send_daily_report():
    """Ежедневный отчет"""
    print("#" * 20)
    try:
        send_mail(
            "Отчет",
            f"Ежедневный отчет",
            settings.EMAIL_HOST_USER,
            [getattr(settings, 'ADMIN_EMAIL', 'example@gmail.com')],
            fail_silently=False,
        )
    except Exception as exc: 
        print(f"send_daily_report send_mail failed: {exc}")
        return f"error: {exc}"
    return "Ok"


# =====================================================
# ЗАДАЧИ ДЛЯ ТЕСТИРОВАНИЯ
# =====================================================

@shared_task
def generate_users_report_task():
    """Генерация CSV-отчёта пользователей"""
    User = get_user_model()
    
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    file_path = reports_dir / "users_report.csv"

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "email", "is_active"])

        for user in User.objects. all():
            email = getattr(user, 'email', '')
            writer.writerow([user.id, email, user.is_active])

    return str(file_path)


@shared_task
def deactivate_inactive_users_task(days=30):
    """Деактивация неактивных пользователей"""
    User = get_user_model()
    
    threshold = timezone.now() - timedelta(days=days)

    qs = User.objects.filter(
        is_active=True,
        last_login__lt=threshold
    )

    updated_count = qs.update(is_active=False)
    return updated_count


@shared_task
def send_admin_stats_task():
    """Email-статистика администратору"""
    User = get_user_model()
    
    total = User.objects.count()
    active = User.objects.filter(is_active=True).count()

    message = (
        f"Всего пользователей: {total}\n"
        f"Активных: {active}"
    )

    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', None) or settings.EMAIL_HOST_USER
        send_mail(
            subject="Статистика пользователей",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[admin_email],
            fail_silently=False,
        )
    except Exception as exc:
        print(f"send_admin_stats_task failed: {exc}")
        return f"error: {exc}"

    return True
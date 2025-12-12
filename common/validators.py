from rest_framework.exceptions import ValidationError
from datetime import date, datetime

def birthday_token(value):
    request = value.context.get('request')
    if not request:
        return

    user_data = request.auth  # payload JWT

    if not user_data:
        raise ValidationError('Вы должны быть авторизованы.')

    birthday = user_data.get('birthday')

    if not birthday:
        raise ValidationError('Укажите свою дату рождения.')

    try:
        # birthday из токена всегда строка, поэтому парсим как ISO
        birthdate = datetime.fromisoformat(str(birthday)).date()
    except Exception:
        raise ValidationError('Неверный формат даты рождения.')

    # возраст 18+
    today = date.today()
    age = today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )

    if age < 18:
        raise ValidationError('Вам должно быть 18 лет, чтобы создавать продукт.')

    return value

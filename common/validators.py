from rest_framework.exceptions import ValidationError
from datetime import date, datetime

def birthday_token(value):
    request = value.context.get('request', None)
    if not request:
        return
    
    user_data = request.auth

    if not user_data:
        raise ValidationError('Вы должны быть авторизованы')
    
    birthday = user_data.get('birthday')
    
    if not birthday:
        raise ValidationError('Укажите свою дату рождения')
    
    try:
        birthdate = datetime.fromisoformat(birthday).data()
    except:
        raise ValidationError('Неверный формат даты рождения')
    
    min_age = 18

    today = date.today()
    age = today.year - birthdate.year -(
        (today.month, today.day) < (birthdate.month, birthdate.day )
    )
    if age < min_age:
        raise ValidationError('Вам должно быть 18 лет, чтобы создать продукт')
    
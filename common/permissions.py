from rest_framework.permissions import BasePermission, SAFE_METHODS
from datetime import timedelta
from django.utils import timezone

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
            and request.user.is_superuser)

class IsOwner(BasePermission):
    """
    Обычный юзер:
    - Может смотреть список (GET)
    - Может создавать (POST)
    - Не является персоналом (staff)
    """
    def has_permission(self, request, view):
        return bool(request.user and  request.user.is_authenticated
            and not request.user.is_staff)
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsModerator(BasePermission):
    """
    Модератор (Staff):
    - Может смотреть (GET)
    - НЕ может создавать (POST)
    """

    def has_permission(self, request, view):
        # если юзер не персонал - то он не модератор
        if not (request.user and request.user.is_authenticated 
            and request.user.is_staff):
            return False
        # если метод безопасен то разрешаем 
        if request.method in SAFE_METHODS:
            return True
        # запрешаем методы POST/PUT/DELETE
        return False
    
    
class IsAnonymous(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return False


class CanEditWithin15Minutes(BasePermission):
    def has_object_permission(self, request, view, obj):
        time_passed = timezone.now() - obj.created_at
        return time_passed <= timedelta(minutes=1)
    

class CreateProductsPermission(BasePermission):
    """
    только сотрудникам нельзя создавать продукт
    
    """
    def has_permission(self, request, view):
        if request.method == "POST":
            return (
                request.user.is_superuser or
                (request.user.is_authenticated and not request.user.is_staff)
            )


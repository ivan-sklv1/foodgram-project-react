from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Класс пользователя."""

    def __str__(self):
        return self.username

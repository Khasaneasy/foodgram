from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models


from .constants import (
    FIRST_NAME_LENGTH, LAST_NAME_LENGTH, EMAIL_LENGTH)


class Profile(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    first_name = models.CharField(
        ('first name'),
        max_length=FIRST_NAME_LENGTH,
        blank=False
    )
    last_name = models.CharField(
        ('last name'),
        max_length=LAST_NAME_LENGTH,
        blank=False
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=EMAIL_LENGTH,
        unique=True
    )
    avatar = models.ImageField(
        upload_to='users/images/',
        default=None,
        verbose_name="Аватар",
    )

    def clean(self):
        super().clean()
        if "me" in self.username:
            raise ValidationError(
                ('Имя пользователя не может содержать "me".'),
                code='invalid_username'
            )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['first_name', 'last_name', 'username', 'email']

    def __str__(self):
        return self.email


class Subscribe(models.Model):
    follower = models.ForeignKey(
        Profile,
        verbose_name='Подписчик',
        related_name='follower',
        on_delete=models.CASCADE
    )

    following = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Пользователь',
    )

    class Meta:
        ordering = ['follower', 'following']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['following', 'follower'],
                name='unique follow',
            ),
            models.CheckConstraint(
                check=~models.Q(following=models.F('follower')),
                name='no_self_subscription'
            )
        ]

    def __str__(self):
        return f'{self.follower} is subscribed to {self.following}'

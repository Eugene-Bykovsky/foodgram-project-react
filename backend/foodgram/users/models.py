from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        verbose_name='Уникальный юзернейм',
        help_text='Введите уникальный юзернейм. Обязательное поле.',
        unique=True
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль',
        help_text='Введите пароль. Обязательное поле.'
    )
    email = models.EmailField(
        max_length=254,
        verbose_name='Адрес электронной почты. Обязательное поле.',
        help_text='Введите email',
        unique=True
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        help_text='Введите имя. Обязательное поле.'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        help_text='Введите фамилию. Обязательное поле.'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='subscriber'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscription'
    )
    added_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='subscription_unique'
            )
        ]
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'Пользователь {self.user} подписан на {self.author}'

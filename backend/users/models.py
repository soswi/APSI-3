from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
	username_validator = RegexValidator(
		regex=r'^[A-Za-z0-9_.-]+$',
		message='Username may contain only letters, numbers, dots, dashes, and underscores.',
	)
	ascii_validator = RegexValidator(
		regex=r'^[\x00-\x7F]+$',
		message='Username must contain only ASCII characters.',
	)

	username = models.CharField(
		max_length=30,
		unique=True,
		validators=[
			MinLengthValidator(3),
			MaxLengthValidator(30),
			username_validator,
			ascii_validator,
		],
	)
	email = models.EmailField(unique=True)
	preference_greenery = models.PositiveSmallIntegerField(default=70)
	preference_noise = models.PositiveSmallIntegerField(default=55)
	preference_air_quality = models.PositiveSmallIntegerField(default=60)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(default=timezone.now)

	objects = UserManager()

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	def __str__(self) -> str:
		return f'{self.username} <{self.email}>'

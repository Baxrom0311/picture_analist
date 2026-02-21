"""
User model - Custom user with role, credits, and profile fields.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import transaction
from django.db.models import F
from django.conf import settings


class User(AbstractUser):
    """
    Custom User model extending AbstractUser.

    Roles:
        - artist: uploads and gets artwork evaluated
        - admin: manages the system
        - judge: reviews AI evaluations (optional)
    """

    ROLE_CHOICES = [
        ('artist', 'Artist'),
        ('admin', 'Admin'),
        ('judge', 'Judge'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='artist',
        verbose_name='Rol'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefon'
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Bio'
    )
    credits = models.IntegerField(
        default=10,
        verbose_name='Kreditlar'
    )

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def has_credits(self):
        """Check if user has at least 1 credit."""
        return self.credits > 0

    def deduct_credit(self):
        """Deduct one credit from user."""
        with transaction.atomic():
            updated = self.__class__.objects.filter(
                pk=self.pk,
                credits__gt=0,
            ).update(credits=F('credits') - 1)
            if not updated:
                self.refresh_from_db(fields=['credits'])
                return False
            self.refresh_from_db(fields=['credits'])
            return True

    def add_credits(self, amount):
        """Add credits to user account."""
        with transaction.atomic():
            self.__class__.objects.filter(pk=self.pk).update(credits=F('credits') + amount)
            self.refresh_from_db(fields=['credits'])

    def save(self, *args, **kwargs):
        # Set default credits for new users
        if not self.pk and self.credits == 0:
            self.credits = getattr(settings, 'DEFAULT_USER_CREDITS', 10)
        super().save(*args, **kwargs)

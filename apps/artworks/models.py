"""
Artwork and Category models.
"""
import logging

from django.db import models
from django.conf import settings

from core.validators import validate_image_size, validate_image_format

logger = logging.getLogger(__name__)


class Category(models.Model):
    """
    Evaluation category (e.g., Composition, Technique, Creativity).
    Each category has a weight percentage used in weighted average scoring.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nomi (EN)'
    )
    # name_uz handled by modeltranslation
    description = models.TextField(
        blank=True,
        verbose_name='Tavsif'
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Vazn (%)',
        help_text='Foizdagi vazn (jami 100% bo\'lishi kerak)'
    )
    criteria = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Mezonlar',
        help_text='Baholash mezonlari (JSON formatda)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol'
    )

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering = ['name']

    def __str__(self):
        return f"{self.name_uz} ({self.weight}%)"


class Artwork(models.Model):
    """
    Artwork uploaded by a user for AI evaluation.
    Tracks image metadata and evaluation status.
    """
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('processing', 'Baholanmoqda'),
        ('completed', 'Baholangan'),
        ('failed', 'Xatolik'),
    ]
    EVALUATION_SCHEME_CHOICES = [
        ('art_history', 'Sanʼatshunoslik (yozma)'),
        ('painting', 'Rangtasvir / Professional taʼlim: rangtasvir'),
        ('design_cg_photo', 'Dizayn: kompyuter grafikasi va badiiy foto'),
        ('design_ad_graphics', 'Dizayn: reklama va amaliy grafika'),
        ('design_interior_industrial', 'Dizayn: interyer / sanoat dizayni'),
        ('design_fashion_textile', 'Dizayn: libos va gazlamalar'),
        ('applied_art', 'Amaliy sanʼat'),
        ('sculpture', 'Haykaltaroshlik'),
        ('graphics', 'Grafika'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='artworks',
        verbose_name='Foydalanuvchi'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Sarlavha'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Tavsif'
    )
    image = models.ImageField(
        upload_to='artworks/%Y/%m/%d/',
        validators=[validate_image_size, validate_image_format],
        verbose_name='Rasm'
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='S3 URL'
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name='Fayl hajmi (bytes)'
    )
    width = models.IntegerField(
        default=0,
        verbose_name='Kenglik (px)'
    )
    height = models.IntegerField(
        default=0,
        verbose_name='Balandlik (px)'
    )
    format = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Format'
    )
    evaluation_scheme = models.CharField(
        max_length=40,
        choices=EVALUATION_SCHEME_CHOICES,
        default='painting',
        verbose_name='Baholash yoʻnalishi'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Holat'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan')

    class Meta:
        verbose_name = 'San\'at asari'
        verbose_name_plural = 'San\'at asarlari'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_artwork_user_date'),
            models.Index(fields=['status', '-created_at'], name='idx_artwork_status_date'),
            models.Index(fields=['status'], name='idx_artwork_status'),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def save(self, *args, **kwargs):
        """Auto-populate image metadata on save."""
        if self.image and not self.file_size:
            self.file_size = self.image.size
            try:
                from PIL import Image
                img = Image.open(self.image)
                self.width, self.height = img.size
                self.format = img.format.lower() if img.format else ''
                if hasattr(self.image, 'seek'):
                    self.image.seek(0)
            except Exception as exc:
                logger.warning(
                    "Failed to extract metadata for artwork %s: %s",
                    self.pk,
                    exc,
                )
        super().save(*args, **kwargs)

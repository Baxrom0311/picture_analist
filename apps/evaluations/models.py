"""
Evaluation, CategoryScore, and EvaluationHistory models.
"""
from django.db import models
from django.conf import settings


class Evaluation(models.Model):
    """
    AI evaluation result for an artwork.
    Stores LLM metadata, total score, and raw response.
    """
    artwork = models.OneToOneField(
        'artworks.Artwork',
        on_delete=models.CASCADE,
        related_name='evaluation',
        verbose_name='San\'at asari'
    )

    # LLM metadata
    llm_provider = models.CharField(
        max_length=50,
        default='claude',
        verbose_name='LLM Provider'
    )
    llm_model = models.CharField(
        max_length=100,
        verbose_name='LLM Model'
    )
    prompt_version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name='Prompt versiyasi'
    )

    # Results
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Umumiy ball'
    )
    summary = models.TextField(
        blank=True,
        verbose_name='Xulosa'
    )
    grade = models.CharField(
        max_length=2,
        blank=True,
        verbose_name='Baho'
    )
    raw_response = models.JSONField(
        default=dict,
        verbose_name='LLM to\'liq javobi'
    )

    # Performance metrics
    processing_time = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=0,
        verbose_name='Qayta ishlash vaqti (soniya)'
    )
    api_cost = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='API narxi (USD)'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan')

    class Meta:
        verbose_name = 'Baholash'
        verbose_name_plural = 'Baholashlar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='idx_eval_created'),
            models.Index(fields=['artwork'], name='idx_eval_artwork'),
        ]

    def __str__(self):
        return f"Evaluation #{self.pk} - {self.artwork.title} ({self.total_score})"


class CategoryScore(models.Model):
    """
    Score for a specific category within an evaluation.
    Contains the score, feedback, strengths, and improvements.
    """
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='category_scores',
        verbose_name='Baholash'
    )
    category = models.ForeignKey(
        'artworks.Category',
        on_delete=models.CASCADE,
        related_name='scores',
        verbose_name='Kategoriya'
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Ball (0-100)'
    )
    feedback = models.TextField(
        blank=True,
        verbose_name='Tahlil'
    )
    strengths = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Kuchli tomonlar'
    )
    improvements = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Yaxshilanish tavsiyalari'
    )

    class Meta:
        verbose_name = 'Kategoriya balli'
        verbose_name_plural = 'Kategoriya ballari'
        unique_together = ['evaluation', 'category']
        ordering = ['category__name']

    def __str__(self):
        return f"{self.category.name}: {self.score}"


class EvaluationHistory(models.Model):
    """
    Audit log for evaluation lifecycle events.
    """
    ACTION_CHOICES = [
        ('started', 'Boshlandi'),
        ('processing', 'Qayta ishlanmoqda'),
        ('completed', 'Yakunlandi'),
        ('failed', 'Xatolik'),
        ('retried', 'Qayta urinildi'),
    ]

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Baholash'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Harakat'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Xabar'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Qo\'shimcha ma\'lumotlar'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Vaqt')

    class Meta:
        verbose_name = 'Baholash tarixi'
        verbose_name_plural = 'Baholash tarixlari'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['evaluation', '-created_at'], name='idx_history_eval_date'),
        ]

    def __str__(self):
        return f"{self.evaluation} - {self.get_action_display()}"

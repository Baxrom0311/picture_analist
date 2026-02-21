"""
Django Admin configuration for Evaluations app.
"""
from django.contrib import admin
from .models import Evaluation, CategoryScore, EvaluationHistory


class CategoryScoreInline(admin.TabularInline):
    model = CategoryScore
    extra = 0
    readonly_fields = ('category', 'score', 'feedback', 'strengths', 'improvements')
    can_delete = False


class EvaluationHistoryInline(admin.TabularInline):
    model = EvaluationHistory
    extra = 0
    readonly_fields = ('action', 'message', 'metadata', 'created_at')
    can_delete = False


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'artwork', 'total_score', 'grade', 'llm_model', 'processing_time', 'api_cost', 'created_at')
    list_filter = ('llm_provider', 'grade', 'created_at')
    search_fields = ('artwork__title', 'artwork__user__username')
    readonly_fields = (
        'artwork', 'llm_provider', 'llm_model', 'prompt_version',
        'total_score', 'summary', 'grade', 'raw_response',
        'processing_time', 'api_cost', 'created_at'
    )
    inlines = [CategoryScoreInline, EvaluationHistoryInline]
    ordering = ('-created_at',)


@admin.register(CategoryScore)
class CategoryScoreAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'category', 'score')
    list_filter = ('category',)
    readonly_fields = ('evaluation', 'category', 'score', 'feedback', 'strengths', 'improvements')


@admin.register(EvaluationHistory)
class EvaluationHistoryAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'action', 'message', 'created_at')
    list_filter = ('action', 'created_at')
    readonly_fields = ('evaluation', 'action', 'message', 'metadata', 'created_at')

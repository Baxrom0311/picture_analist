"""
Django Admin configuration for Users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'credits', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profil', {
            'fields': ('role', 'phone', 'avatar', 'bio', 'credits'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profil', {
            'fields': ('role', 'email', 'credits'),
        }),
    )

    actions = ['add_10_credits', 'reset_credits']

    @admin.action(description='10 ta kredit qo\'shish')
    def add_10_credits(self, request, queryset):
        for user in queryset:
            user.add_credits(10)
        self.message_user(request, f'{queryset.count()} foydalanuvchiga 10 kredit qo\'shildi.')

    @admin.action(description='Kreditlarni 10 ga qaytarish')
    def reset_credits(self, request, queryset):
        queryset.update(credits=10)
        self.message_user(request, f'{queryset.count()} foydalanuvchi krediti qaytarildi.')

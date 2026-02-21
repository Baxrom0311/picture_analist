"""
Django Admin configuration for Artworks app.
"""
from django.contrib import admin
from .models import Category, Artwork


from modeltranslation.admin import TranslationAdmin

@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ('name', 'weight', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('weight', 'is_active')
    ordering = ('name',)
    
    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'format', 'file_size_display', 'created_at')
    list_filter = ('status', 'format', 'created_at')
    search_fields = ('title', 'user__username', 'description')
    readonly_fields = ('file_size', 'width', 'height', 'format', 'image_url', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    raw_id_fields = ('user',)

    def file_size_display(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024:.1f} KB"
        return "-"
    file_size_display.short_description = "Hajm"

import os
import sys
import django

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.artworks.models import Category
from django.utils import translation

# Mapping: name_uz (current) -> (name_en, name_ru)
TRANSLATIONS = {
    'Kompozitsiya': ('Composition', 'Композиция'),
    'Kreativlik': ('Creativity', 'Креативность'),
    "Rang va yorug'lik": ('Color and Light', 'Цвет и свет'),
    'Texnika': ('Technique', 'Техника'),
    "Umumiy ta'sir": ('Overall Impact', 'Общее впечатление'),
}

def update_translations():
    # Activate Uzbek to find by Uzbek name (since default is 'uz')
    translation.activate('uz')
    
    count = 0
    for cat in Category.objects.all():
        # Clean current name (strip spaces)
        name_uz = cat.name.strip()
        
        if name_uz in TRANSLATIONS:
            en, ru = TRANSLATIONS[name_uz]
            
            # Update specific fields
            cat.name_en = en
            cat.name_ru = ru
            
            # Ensure name_uz is explicit (it should be allowed)
            cat.name_uz = name_uz
            
            cat.save()
            print(f"Updated: {name_uz} -> {en}, {ru}")
            count += 1
        else:
            print(f"Skipped: {name_uz} (No translation found)")
            
    print(f"Total updated: {count}")

if __name__ == '__main__':
    update_translations()

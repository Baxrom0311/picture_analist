#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Monkeypatch for Django 4.2 + Python 3.14 compatibility
# Fixes AttributeError: 'super' object has no attribute 'dicts' in BaseContext.__copy__
try:
    import django.template.context
    
    def fixed_context_copy(self):
        # Python 3.14 object.__copy__ does not support setting attributes if not present in __dict__?
        # Or simply, super().__copy__() returns a new instance, but we need to ensure it's initialized correctly.
        # simpler approach: create new instance and copy dicts
        duplicate = self.__class__()
        duplicate.dicts = self.dicts[:]
        duplicate.autoescape = self.autoescape
        duplicate.use_l10n = self.use_l10n
        duplicate.use_tz = self.use_tz
        duplicate.template_name = self.template_name
        duplicate.render_context = self.render_context.copy()
        # copy other attributes if needed, but existing django implementation relied on copy.copy(self) via super
        return duplicate

    # Actually, the easier fix is just to implement __copy__ without super() if super is failing
    # But let's try a safer patch that mimics the original intent but handles the 3.14 change
    
    def patched_copy(self):
        import copy
        # Create a new instance
        duplicate = copy.copy(super(django.template.context.BaseContext, self))
        # This is where it fails if super().__copy__ returns something that is not writable or different
        # Let's try to just assign directly if it allows
        duplicate.dicts = self.dicts[:]
        return duplicate

    # The most robust fix for the test runner crash:
    def safe_copy(self):
        # Fix for Python 3.14 + Django 4.2: Use __new__ to bypass __init__ (needed for RequestContext)
        import copy
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__ = self.__dict__.copy()
        
        # Ensure deep copy of dicts if present (Django specific)
        if hasattr(self, 'dicts'):
            duplicate.dicts = self.dicts[:]
        
        # render_context needs copy too if present
        if hasattr(self, 'render_context'):
             duplicate.render_context = copy.copy(self.render_context)
             
        return duplicate

    django.template.context.BaseContext.__copy__ = safe_copy
except ImportError:
    pass



def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

from django.contrib import admin

from .models import Config, Control, Value

admin.site.register(Config)
admin.site.register(Control)
admin.site.register(Value)
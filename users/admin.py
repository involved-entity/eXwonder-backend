from django.contrib import admin

from users.models import ExwonderUser


@admin.register(ExwonderUser)
class ExwonderUserAdmin(admin.ModelAdmin):
    list_display = 'id', 'username', 'email', 'date_joined'
    list_display_links = 'id', 'username', 'email'
    ordering = '-date_joined',

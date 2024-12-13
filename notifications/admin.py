from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = "recipient", "post", "time_added"
    list_display_links = "recipient", "post"
    list_per_page = 50
    ordering = ("-time_added",)
    search_fields = "recipient__username", "post__id"

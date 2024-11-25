from django.contrib import admin, messages

from users.models import ExwonderUser, Follow


class EmailFilter(admin.SimpleListFilter):
    title = "has email"
    parameter_name = "email_exists"

    def lookups(self, request, model_admin):
        return (("true", "Yes"), ("false", "No"))

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(email__isnull=False)
        elif self.value() == "false":
            return queryset.filter(email__isnull=True)
        return queryset


@admin.register(ExwonderUser)
class ExwonderUserAdmin(admin.ModelAdmin):
    fields = (
        "username",
        "email",
        "avatar",
        "timezone",
        "is_2fa_enabled",
        "last_login",
        "penultimate_login",
        "is_superuser",
        "is_active",
    )
    readonly_fields = "penultimate_login", "last_login"
    list_display = "id", "username", "email", "date_joined", "is_superuser"
    list_display_links = "id", "username", "email"
    ordering = ("-date_joined",)
    list_per_page = 50
    actions = "set_superuser", "remove_superuser"
    search_fields = "username", "email"
    list_filter = "is_superuser", EmailFilter

    @admin.action(description="Give superuser permissions")
    def set_superuser(self, request, queryset):
        count = queryset.update(is_superuser=True)
        self.message_user(request, message=f"Give superuser perms to {count} users", level=messages.WARNING)

    @admin.action(description="Remove superuser permissions")
    def remove_superuser(self, request, queryset):
        count = queryset.update(is_superuser=False)
        self.message_user(request, message=f"Remove superuser perms at {count} users", level=messages.WARNING)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = "id", "follower__username", "following__username"
    ordering = ("-id",)
    search_fields = "follower__username", "following__username"

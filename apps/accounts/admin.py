from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, School, Learner

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("email", "username")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("Platform specific", {"fields": ("role",)}),
    )

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("school_name", "region", "district", "is_active")
    list_filter = ("region", "district", "is_active")
    search_fields = ("school_name",)

@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ("get_email", "school", "class_level", "enrolled_at")
    list_filter = ("class_level", "school")
    search_fields = ("user__email", "school__school_name")

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"

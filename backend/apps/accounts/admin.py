from django.contrib import admin

from .models import Brand, Profile


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "brand", "role"]
    list_filter = ["brand", "role"]

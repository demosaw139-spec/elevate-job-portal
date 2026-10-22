from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Application, Company, Job, SavedJob, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Portal access", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "industry", "location", "verified")
    search_fields = ("name", "owner__username", "industry")
    list_filter = ("verified", "industry")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "work_mode", "status", "created_at")
    list_filter = ("status", "work_mode", "employment_type")
    search_fields = ("title", "company__name", "location")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "candidate", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job__title", "candidate__username", "candidate__email")


admin.site.register(SavedJob)
admin.site.site_header = "Elevate platform administration"
admin.site.site_title = "Elevate Admin"
admin.site.index_title = "Platform operations"

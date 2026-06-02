from django.contrib import admin

class BaseAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True
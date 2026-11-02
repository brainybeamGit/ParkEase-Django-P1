from django.contrib import admin
from .models import UserProfile, Vehicle

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'mobile_number')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'user', 'vehicle_type', 'make', 'model', 'is_ev', 'is_primary', 'created_at')
    list_filter = ('vehicle_type', 'is_ev', 'is_primary')
    search_fields = ('registration_number', 'make', 'model', 'user__username', 'user__email')

from django.contrib import admin
from .models import LotOwnerProfile, ParkingLot

@admin.register(LotOwnerProfile)
class LotOwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'owner_type', 'id_type', 'id_number', 'is_verified', 'created_at')
    list_filter = ('owner_type', 'id_type', 'is_verified')
    search_fields = ('user__username', 'user__email', 'id_number', 'city')

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'space_type', 'city', 'total_capacity', 'hourly_rate', 'status', 'created_at')
    list_filter = ('status', 'space_type', 'city')
    search_fields = ('name', 'owner__username', 'area', 'city', 'pin_code')
    list_editable = ('status',)

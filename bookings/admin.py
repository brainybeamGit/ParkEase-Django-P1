from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vehicle', 'parking_lot', 'booking_type', 'start_time', 'payment_status', 'booking_status')
    list_filter = ('booking_type', 'payment_status', 'booking_status')
    search_fields = ('user__username', 'vehicle__registration_number', 'parking_lot')

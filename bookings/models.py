from django.db import models
from django.contrib.auth.models import User
from accounts.models import Vehicle

class Booking(models.Model):
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('refund_requested', 'Refund Requested'),
        ('failed', 'Failed'),
    ]

    BOOKING_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    BOOKING_TYPE_CHOICES = [
        ('advance', 'Advance Reservation'),
        ('drive_up', 'Drive-Up / Pay on Arrival'),
        ('monthly', 'Monthly Subscription'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    lot = models.ForeignKey(
        'lot_owner_panel.ParkingLot',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name="Parking Facility (Relational Link)"
    )
    slot = models.ForeignKey(
        'lot_owner_panel.ParkingSlot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name="Assigned Parking Slot / Bay"
    )
    parking_lot = models.CharField(max_length=220, verbose_name="Parking Location / Facility")
    booking_type = models.CharField(max_length=30, choices=BOOKING_TYPE_CHOICES, default='advance')
    start_time = models.DateTimeField(verbose_name="Start Date & Time")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="End Date & Time")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total Fee (INR)")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='active')
    qr_code_token = models.CharField(max_length=64, blank=True, default='')

    
    entry_time = models.DateTimeField(null=True, blank=True, verbose_name="Gate Entry Scan Time")
    exit_time = models.DateTimeField(null=True, blank=True, verbose_name="Gate Exit Scan Time")
    is_parked = models.BooleanField(default=False, verbose_name="Vehicle Currently Parked Inside")
     
    overstay_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Overstay Duration (Hours)")
    overstay_fine = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Overstay Extra Fee (INR)")
    overstay_paid = models.BooleanField(default=False, verbose_name="Overstay Fine Settled")

    razorpay_order_id = models.CharField(max_length=100, blank=True, default='', verbose_name="Razorpay Order ID")
    razorpay_payment_id = models.CharField(max_length=100, blank=True, default='', verbose_name="Razorpay Payment ID")


    refund_reason = models.TextField(blank=True, default='', verbose_name="Cancellation / Refund Reason")
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Approved Refund Amount (INR)")
    refund_requested_at = models.DateTimeField(null=True, blank=True, verbose_name="Refund Requested Timestamp")
    refund_processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Refund Processed Timestamp")
    refund_transaction_id = models.CharField(max_length=100, blank=True, default='', verbose_name="Refund Gateway Txn ID")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        reg = self.vehicle.registration_number if self.vehicle else 'No Vehicle'
        return f"Booking #{self.id} - {self.parking_lot} ({reg}) [{self.booking_status}]"

    @property
    def latest_extension_request(self):
        return self.extension_requests.order_by('-created_at').first()

    @property
    def has_pending_extension(self):
        return self.extension_requests.filter(status='pending').exists()

    @property
    def user_review(self):
        from lot_owner_panel.models import LotReview
        ref = f"PE-BK-{self.id}"
        rev = LotReview.objects.filter(booking_ref=ref).first()
        if not rev:
            rev = LotReview.objects.filter(booking_ref=str(self.id)).first()
        return rev


class BookingExtensionRequest(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='extension_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_extension_requests')
    additional_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name="Additional Hours")
    current_end_time = models.DateTimeField(verbose_name="Original Scheduled End Time")
    requested_new_end_time = models.DateTimeField(verbose_name="Requested New End Time")
    additional_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Additional Tariff (INR)")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    
    conflict_detected = models.BooleanField(default=False, verbose_name="Overlap with subsequent booking")
    conflicting_booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conflicting_extensions',
        verbose_name="Overlapping Second User Booking"
    )
    conflict_details = models.TextField(blank=True, default='', verbose_name="Conflict / Overlap Information")

    
    assigned_lot = models.ForeignKey(
        'lot_owner_panel.ParkingLot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='extension_reassigned_lots',
        verbose_name="Reassigned Parking Lot"
    )
    assigned_slot = models.ForeignKey(
        'lot_owner_panel.ParkingSlot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='extension_reassigned_slots',
        verbose_name="Reassigned Parking Slot / Bay"
    )
    owner_note = models.TextField(blank=True, default='', verbose_name="Owner Review Note / Vacate Instruction")

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking Extension Request"
        verbose_name_plural = "Booking Extension Requests"

    def __str__(self):
        return f"Extension Req #{self.id} for Booking #{self.booking_id} (+{self.additional_hours} hrs) [{self.status}]"

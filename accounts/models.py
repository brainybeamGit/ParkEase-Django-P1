from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import re

def normalize_registration_number(reg_str):
    """
    Normalizes a vehicle registration number:
    - Strips leading/trailing whitespace
    - Converts to uppercase
    - Collapses multiple hyphens/spaces into clean single space
    Example: 'dl-01-ab-1234' -> 'DL 01 AB 1234'
             'mh12cd5678' -> 'MH 12 CD 5678' (if spaced) or preserved clean
    """
    if not reg_str:
        return ""
    cleaned = reg_str.strip().upper()
    cleaned = re.sub(r'[\s\-_\.]+', ' ', cleaned)
    return cleaned


class UserProfile(models.Model):
    """
    Extended user profile for contact details and parking account settings.
    """
    ROLE_CHOICES = [
        ('driver', 'Driver / Customer'),
        ('owner', 'Parking Lot Owner'),
        ('admin', 'Platform Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='driver')
    mobile_number = models.CharField(max_length=25, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile ({self.mobile_number or 'No Mobile'})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


class Vehicle(models.Model):
    """
    Motorist Registered Vehicle Model.
    Supports primary vehicle tracking, multiple vehicles per user,
    EV charging preferences, and type categorization.
    """
    VEHICLE_TYPE_CHOICES = [
        ('two_wheeler', 'Two-wheeler (Bike / Scooter)'),
        ('car', 'Car (Hatchback / Sedan)'),
        ('suv', 'SUV'),
        ('other', 'Other supported vehicle'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    registration_number = models.CharField(max_length=25, db_index=True)
    vehicle_type = models.CharField(max_length=30, choices=VEHICLE_TYPE_CHOICES, default='car')
    make = models.CharField(max_length=60, blank=True, default='', verbose_name="Vehicle Make / Brand")
    model = models.CharField(max_length=60, blank=True, default='', verbose_name="Vehicle Model")
    is_ev = models.BooleanField(default=False, verbose_name="Electric Vehicle (EV)")
    is_primary = models.BooleanField(default=True, verbose_name="Primary Vehicle")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"

    def save(self, *args, **kwargs):
        self.registration_number = normalize_registration_number(self.registration_number)
        if self.is_primary:
            Vehicle.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        desc = f"{self.make} {self.model}".strip()
        label = f"{self.registration_number}"
        if desc:
            label += f" ({desc})"
        if self.is_ev:
            label += " [EV]"
        return label


class PasswordResetOTP(models.Model):
    """
    6-Digit One-Time Password (OTP) for Secure Driver & Owner Password Reset.
    Valid for 10 minutes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_otps')
    email = models.EmailField(db_index=True)
    otp_code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Password Reset OTP"
        verbose_name_plural = "Password Reset OTPs"

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        status = "Used" if self.is_used else ("Expired" if not self.is_valid() else "Active")
        return f"OTP {self.otp_code} for {self.email} ({status})"


class EmailDeliveryLog(models.Model):
    """
    Comprehensive Email Delivery Tracking & Audit Log.
    Tracks all platform notifications across Drivers, Space Owners, and Administrators.
    """
    ROLE_CHOICES = [
        ('driver', 'Driver / Customer'),
        ('owner', 'Parking Owner'),
        ('admin', 'Platform Admin'),
        ('staff', 'Support Staff'),
        ('other', 'Other Recipient'),
    ]

    STATUS_CHOICES = [
        ('sent', 'Delivered / Sent'),
        ('simulated', 'Simulated (Dev Mode)'),
        ('failed', 'Failed Delivery'),
    ]

    recipient = models.EmailField(db_index=True)
    recipient_name = models.CharField(max_length=150, blank=True, default='')
    recipient_role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='driver')
    event_type = models.CharField(max_length=100, db_index=True)
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    error_message = models.TextField(blank=True, default='')
    message_id = models.CharField(max_length=100, blank=True, default='')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Email Delivery Log"
        verbose_name_plural = "Email Delivery Logs"

    def __str__(self):
        return f"[{self.sent_at.strftime('%Y-%m-%d %H:%M')}] [{self.status.upper()}] {self.event_type} -> {self.recipient}"

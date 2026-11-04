from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PlatformSetting(models.Model):
    
    commission_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    overstay_fine_hourly = models.DecimalField(max_digits=7, decimal_places=2, default=100.00)
    min_hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=20.00)
    max_hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=500.00)
    grace_period_minutes = models.PositiveIntegerField(default=15)
    razorpay_active = models.BooleanField(default=True)
    auto_payout_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ParkEase Settings (Commission: {self.commission_rate_pct}%)"


class PlatformCoupon(models.Model):
    
    code = models.CharField(max_length=50, unique=True)
    discount_pct = models.PositiveIntegerField(default=20)
    max_discount_amount = models.DecimalField(max_digits=7, decimal_places=2, default=150.00)
    valid_until = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Coupon: {self.code} ({self.discount_pct}% off)"


class PlatformComplaint(models.Model):
    
    STATUS_CHOICES = [
        ('open', 'Open / New'),
        ('investigating', 'In Investigation'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected / Dismissed'),
    ]

    ticket_id = models.CharField(max_length=30, unique=True)
    user_type = models.CharField(max_length=20, default='Driver')  # Driver or Owner
    complainant_name = models.CharField(max_length=150)
    contact_email = models.CharField(max_length=150, blank=True, default='')
    booking_ref = models.CharField(max_length=50, blank=True, default='')
    lot_name = models.CharField(max_length=150, blank=True, default='')
    category = models.CharField(max_length=100, default='Booking Dispute')
    priority = models.CharField(max_length=20, default='Medium')
    description = models.TextField()
    admin_notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.ticket_id}] {self.category} - {self.complainant_name}"


class PlatformAnnouncement(models.Model):
    
    AUDIENCE_CHOICES = [
        ('all', 'All Users & Owners'),
        ('drivers', 'Drivers Only'),
        ('owners', 'Space Owners Only'),
        ('staff', 'Staff & Admins Only'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    audience = models.CharField(max_length=30, choices=AUDIENCE_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_audience_display()})"


class AdminAuditLog(models.Model):
    
    admin_user = models.CharField(max_length=100)
    action = models.CharField(max_length=200)
    target_object = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField(blank=True, null=True, default='127.0.0.1')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.admin_user}: {self.action} on {self.target_object}"




class PlatformFeedback(models.Model):
    
    CATEGORY_CHOICES = [
        ('general', 'General Platform Feedback'),
        ('booking', 'Booking & Parking Experience'),
        ('payments', 'Payment, Tariff & Refund'),
        ('ui_ux', 'Website & User Experience'),
        ('support', 'Customer Care & Support'),
        ('suggestion', 'New Feature Suggestion'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='platform_feedbacks')
    name = models.CharField(max_length=150)
    email = models.EmailField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='general')
    rating = models.PositiveSmallIntegerField(default=5)  # 1 to 5 stars
    message = models.TextField()
    is_reviewed = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback #{self.id} from {self.name} ({self.rating}★) - {self.get_category_display()}"


class AdminNotification(models.Model):
    
    category = models.CharField(max_length=50, default='system')  # owner_verification, lot_approval, dispute, payment, overstay
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({'Read' if self.is_read else 'Unread'})"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=AdminNotification)
def notify_admin_via_email(sender, instance, created, **kwargs):
    if created:
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_admin_notification_email(instance.title, instance.message)
        except Exception:
            pass



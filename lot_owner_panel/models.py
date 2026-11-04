from django.db import models
from django.contrib.auth.models import User

class LotOwnerProfile(models.Model):
    
    OWNER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('property_manager', 'Property Manager'),
    ]

    ID_TYPE_CHOICES = [
        ('aadhaar', 'Aadhaar Card'),
        ('pan', 'PAN Card'),
        ('passport', 'Passport'),
        ('driving_licence', 'Driving Licence'),
        ('voter_id', 'Voter ID'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lot_owner_profile')
    owner_type = models.CharField(max_length=30, choices=OWNER_TYPE_CHOICES, default='individual')
    profile_photo = models.ImageField(upload_to='owners/profiles/', blank=True, null=True)
    
    
    present_address = models.TextField(blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    pin_code = models.CharField(max_length=20, blank=True, default='')

    
    id_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, default='aadhaar')
    id_number = models.CharField(max_length=100)
    id_document = models.FileField(upload_to='owners/id_documents/', blank=True, null=True)

    
    bank_account_holder = models.CharField(max_length=150, blank=True, default='')
    bank_name = models.CharField(max_length=150, blank=True, default='')
    bank_account_number = models.CharField(max_length=50, blank=True, default='')
    bank_ifsc_code = models.CharField(max_length=30, blank=True, default='')
    bank_branch = models.CharField(max_length=150, blank=True, default='')
    bank_account_type = models.CharField(max_length=60, blank=True, default='Current Account / Business')

    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def business_name(self):
        return getattr(self, 'bank_account_holder', '') or f"{self.user.username} Parking"

    @property
    def phone(self):
        if hasattr(self.user, 'profile') and getattr(self.user.profile, 'mobile_number', None):
            return self.user.profile.mobile_number
        return "Not provided"

    @property
    def bank_ifsc(self):
        return self.bank_ifsc_code

    @property
    def average_rating(self):
        from lot_owner_panel.models import LotReview
        from django.db.models import Avg
        res = LotReview.objects.filter(parking_lot__owner=self.user).aggregate(avg=Avg('rating'))['avg']
        return round(float(res), 1) if res else 5.0

    @property
    def total_reviews_count(self):
        from lot_owner_panel.models import LotReview
        return LotReview.objects.filter(parking_lot__owner=self.user).count()

    def __str__(self):
        return f"Owner: {self.user.get_full_name() or self.user.username} ({self.get_owner_type_display()})"


class ParkingLot(models.Model):
   
    SPACE_TYPE_CHOICES = [
        ('open_plot', 'Open plot'),
        ('covered', 'Covered parking'),
        ('basement', 'Basement parking'),
        ('commercial', 'Commercial building'),
        ('residential', 'Residential driveway'),
        ('multilevel', 'Multilevel facility'),
        ('other', 'Other supported space'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parking_lots')
    name = models.CharField(max_length=150, verbose_name="Parking lot name")
    space_type = models.CharField(max_length=50, choices=SPACE_TYPE_CHOICES, default='residential')
    
    
    building_name = models.CharField(max_length=150, blank=True, default='')
    street_address = models.CharField(max_length=255)
    area = models.CharField(max_length=120)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    map_location = models.CharField(max_length=255, blank=True, default='')

    
    total_capacity = models.PositiveIntegerField(default=1)
    supported_vehicles = models.JSONField(default=list)  
    parking_arrangement = models.CharField(max_length=60, default='open_air')
    
    
    operating_hours = models.CharField(max_length=100, default='24/7')
    available_services = models.JSONField(default=list)  
    access_instructions = models.TextField(blank=True, default='')
    space_photo = models.ImageField(upload_to='parking_lots/photos/', blank=True, null=True)

    
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2, default=300.00)
    monthly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=4500.00)
    overnight_rate = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    
    
    bike_rate = models.DecimalField(max_digits=8, decimal_places=2, default=20.00)
    car_rate = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    suv_rate = models.DecimalField(max_digits=8, decimal_places=2, default=70.00)
    ev_rate = models.DecimalField(max_digits=8, decimal_places=2, default=60.00)

    
    peak_hour_surge_pct = models.PositiveIntegerField(default=20)
    min_duration_hours = models.PositiveIntegerField(default=1)
    max_duration_days = models.PositiveIntegerField(default=7)
    monthly_pass_capacity = models.PositiveIntegerField(default=10)
    monthly_pass_auto_renew = models.BooleanField(default=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    is_paused = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, default='')

    
    agreed_terms = models.BooleanField(default=False)
    agreed_privacy = models.BooleanField(default=False)
    confirmed_declaration = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def average_rating(self):
        from django.db.models import Avg
        res = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(float(res), 1) if res else 5.0

    @property
    def total_reviews_count(self):
        return self.reviews.count()

    def __str__(self):
        return f"{self.name} - {self.area}, {self.city} ({self.get_status_display()})"


class ParkingSlot(models.Model):
    
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='slots')
    zone = models.CharField(max_length=60, default='Basement A')
    slot_number = models.CharField(max_length=30)
    vehicle_category = models.CharField(max_length=30, default='Car')  
    status = models.CharField(max_length=30, default='Available')  
    schedule = models.CharField(max_length=100, default='6 AM–11 PM')
    booking_restrictions = models.CharField(max_length=100, default='Min 1 hr, Max 24 hrs')
    maintenance_status = models.CharField(max_length=30, default='Operational')  

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.parking_lot.name} - {self.zone} ({self.slot_number})"


class EVCharger(models.Model):
    
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='ev_chargers')
    charger_id = models.CharField(max_length=50)  
    location = models.CharField(max_length=100, default='Basement Level 1')
    connector_type = models.CharField(max_length=100, default='Type 2 AC / CCS2 DC Fast')
    power_kw = models.DecimalField(max_digits=6, decimal_places=1, default=22.0)
    status = models.CharField(max_length=30, default='Available') 
    rate_per_kwh = models.DecimalField(max_digits=6, decimal_places=2, default=15.00)
    parking_fee_included = models.BooleanField(default=True)
    schedule = models.CharField(max_length=100, default='24/7 Access')
    last_session_kw = models.DecimalField(max_digits=6, decimal_places=1, default=18.5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.charger_id} ({self.parking_lot.name})"


class OwnerPayout(models.Model):
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    period = models.CharField(max_length=100, default='Current Cycle')
    gross_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refunds = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    adjustments = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_payable = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Paid')
    reference = models.CharField(max_length=100, blank=True, default='')
    payout_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payout {self.reference} - ₹{self.net_payable} ({self.status})"


class OwnerNotification(models.Model):
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_notifications')
    category = models.CharField(max_length=50, default='booking')  # booking, arrival, payment, cancellation, approval, maintenance, dispute
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.owner.username}: {self.title}"


class OwnerSupportTicket(models.Model):
    
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Review', 'In Review'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.SET_NULL, null=True, blank=True)
    booking_ref = models.CharField(max_length=100, blank=True, default='')
    category = models.CharField(max_length=100, default='Settlement / Payout')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to='owners/support/', blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Open')
    admin_response = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.status})"


class LotReview(models.Model):
    
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='lot_reviews')
    driver_name = models.CharField(max_length=100, default='Driver')
    booking_ref = models.CharField(max_length=50, default='BK-8942')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    owner_reply = models.TextField(blank=True, default='')
    is_reported = models.BooleanField(default=False)
    report_reason = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parking_lot.name} - {self.rating}★ by {self.driver_name}"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=OwnerNotification)
def notify_owner_via_email(sender, instance, created, **kwargs):
    if created and instance.owner and instance.owner.email:
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_owner_notification_email(instance.owner, instance.title, instance.message)
        except Exception:
            pass


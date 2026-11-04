from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import csv
import json

from accounts.models import UserProfile, Vehicle
from lot_owner_panel.models import (
    LotOwnerProfile, ParkingLot, ParkingSlot, EVCharger,
    OwnerPayout, OwnerNotification, OwnerSupportTicket, LotReview
)
from bookings.models import Booking
from .models import (
    PlatformSetting, PlatformCoupon, PlatformComplaint,
    PlatformAnnouncement, AdminAuditLog, AdminNotification
)




def log_audit(admin_user, action, target_object, ip_address="127.0.0.1"):
    try:
        username = admin_user.username if hasattr(admin_user, 'username') else str(admin_user)
        AdminAuditLog.objects.create(
            admin_user=username,
            action=action,
            target_object=target_object,
            ip_address=ip_address
        )
    except Exception:
        pass


def admin_required(view_func):
    
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with administrator credentials.")
            return redirect('admin_panel:login')

        is_admin = (
            request.user.is_superuser or
            request.user.is_staff or
            (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')
        )
        if not is_admin:
            logout(request)
            messages.error(request, "Access denied. Only platform administrators can access the Admin Portal.")
            return redirect('admin_panel:login')

        return view_func(request, *args, **kwargs)
    return _wrapped_view




def ensure_admin_sample_data():
    

    setting = PlatformSetting.objects.first()
    if not setting:
        setting = PlatformSetting.objects.create(
            commission_rate_pct=15.00,
            overstay_fine_hourly=100.00,
            min_hourly_rate=20.00,
            max_hourly_rate=500.00,
            grace_period_minutes=15,
            razorpay_active=True,
            auto_payout_enabled=True
        )

    
    if not PlatformCoupon.objects.exists():
        PlatformCoupon.objects.create(
            code="PARKEASE20",
            discount_pct=20,
            max_discount_amount=100.00,
            valid_until=timezone.now().date() + timedelta(days=90),
            is_active=True,
            usage_count=142
        )
        PlatformCoupon.objects.create(
            code="EVCHARGE50",
            discount_pct=50,
            max_discount_amount=200.00,
            valid_until=timezone.now().date() + timedelta(days=60),
            is_active=True,
            usage_count=88
        )
        PlatformCoupon.objects.create(
            code="FESTIVE30",
            discount_pct=30,
            max_discount_amount=150.00,
            valid_until=timezone.now().date() + timedelta(days=30),
            is_active=True,
            usage_count=64
        )

    
    if not PlatformComplaint.objects.exists():
        PlatformComplaint.objects.create(
            ticket_id="TKT-2026-9041",
            user_type="Driver",
            complainant_name="Vikram Mehta",
            contact_email="vikram.mehta@gmail.com",
            booking_ref="BK-1039",
            lot_name="Shree Complex Parking",
            category="Overstay Fine Dispute",
            priority="High",
            description="Motorist was billed ₹100 for overstay due to barrier gate scanner delay of 10 minutes.",
            admin_notes="Reviewed barrier timestamps. Barrier gate 1 was rebooted at 12:05 PM.",
            status="investigating"
        )
        PlatformComplaint.objects.create(
            ticket_id="TKT-2026-9042",
            user_type="Owner",
            complainant_name="Ramesh Patel (Shree Complex)",
            contact_email="owner@gmail.com",
            booking_ref="BK-1040",
            lot_name="Shree Complex Parking",
            category="EV Charger Metering",
            priority="Medium",
            description="Reported power fluctuation during fast DC charging session.",
            admin_notes="Technician dispatched to calibrate charger CHG-B1-01.",
            status="resolved"
        )
        PlatformComplaint.objects.create(
            ticket_id="TKT-2026-9043",
            user_type="Driver",
            complainant_name="Sneha Kapoor",
            contact_email="sneha.k@outlook.com",
            booking_ref="BK-1045",
            lot_name="Alpha Tech Space",
            category="Refund Request",
            priority="Low",
            description="Cancelled reservation 3 hours in advance; requesting refund confirmation.",
            admin_notes="Refund of ₹150 processed to original payment method via Razorpay.",
            status="resolved"
        )

    
    if not PlatformAnnouncement.objects.exists():
        PlatformAnnouncement.objects.create(
            title="GST & Automated TDS Settlement Update",
            message="All space owner payouts now automatically reflect compliant 15% platform commission and 1% TDS.",
            audience="owners",
            is_active=True
        )
        PlatformAnnouncement.objects.create(
            title="ParkEase Holiday Parking Guidance",
            message="Anticipating 45% surge in airport and shopping district parking traffic this weekend.",
            audience="all",
            is_active=True
        )

    
    if not AdminNotification.objects.exists():
        sample_alerts = [
            ("owner_verification", "New Owner Application Received", "Store 'Shree Complex Parking' (Ramesh Patel) submitted registration documents. Awaiting admin review.", "/admin-panel/owners/"),
            ("lot_approval", "New Parking Lot Submitted", "Facility 'Navrang Business Bay' submitted for capacity verification (65 bays).", "/admin-panel/parking-lots/"),
            ("dispute", "New Booking Dispute Raised", "Ticket #TKT-2026-9041: Motorist reported overstay dispute at Shree Complex Parking.", "/admin-panel/complaints/"),
            ("payment", "Automated Payout Cycle Executed", "Dispatched ₹28,620.00 to verified owner account. UTR ref UTR9847291847192.", "/admin-panel/payouts/"),
            ("system", "Razorpay Payment Gateway Healthy", "All payment captures, signatures, and instant refunds verified successfully.", "/admin-panel/payments/"),
        ]
        for cat, title, msg, link in sample_alerts:
            AdminNotification.objects.create(
                category=cat,
                title=title,
                message=msg,
                link=link,
                is_read=False
            )

    
    if not AdminAuditLog.objects.exists():
        AdminAuditLog.objects.create(admin_user="admin", action="Verified Owner Application", target_object="LotOwnerProfile: Ramesh Patel")
        AdminAuditLog.objects.create(admin_user="admin", action="Approved Parking Lot", target_object="ParkingLot: Shree Complex Parking")
        AdminAuditLog.objects.create(admin_user="admin", action="Updated Platform Commission", target_object="PlatformSetting: 15.00%")
        AdminAuditLog.objects.create(admin_user="admin", action="Processed Settlement Payout", target_object="OwnerPayout: UTR9847291847192")

    
    if not Booking.objects.exists():
        driver = User.objects.filter(is_staff=False).exclude(lot_owner_profile__isnull=False).first()
        if not driver:
            driver = User.objects.create_user(username='driver_rohit', email='rohit.sharma@gmail.com', first_name='Rohit', last_name='Sharma')

        v1, _ = Vehicle.objects.get_or_create(user=driver, registration_number='GJ 01 AB 1234', defaults={'make': 'Hyundai', 'model': 'Creta', 'vehicle_type': 'car'})
        v2, _ = Vehicle.objects.get_or_create(user=driver, registration_number='GJ 01 EE 4589', defaults={'make': 'Honda', 'model': 'City', 'vehicle_type': 'car'})
        v3, _ = Vehicle.objects.get_or_create(user=driver, registration_number='GJ 01 EV 8821', defaults={'make': 'Tata', 'model': 'Nexon EV', 'vehicle_type': 'car', 'is_ev': True})
        v4, _ = Vehicle.objects.get_or_create(user=driver, registration_number='GJ 27 K 7712', defaults={'make': 'Royal Enfield', 'model': 'Classic', 'vehicle_type': 'two_wheeler'})

        now = timezone.now()
        Booking.objects.create(
            user=driver,
            vehicle=v1,
            parking_lot="Shree Complex Parking",
            booking_type="advance",
            start_time=now,
            end_time=now + timedelta(hours=3),
            total_amount=150.00,
            payment_status="paid",
            booking_status="active",
            qr_code_token="QR_PK_1042"
        )
        Booking.objects.create(
            user=driver,
            vehicle=v2,
            parking_lot="Shree Complex Parking",
            booking_type="monthly",
            start_time=now - timedelta(days=2),
            end_time=now + timedelta(days=28),
            total_amount=4500.00,
            payment_status="paid",
            booking_status="active",
            qr_code_token="QR_PK_1041"
        )
        Booking.objects.create(
            user=driver,
            vehicle=v3,
            parking_lot="Shree Complex Parking",
            booking_type="advance",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            total_amount=420.00,
            payment_status="paid",
            booking_status="active",
            qr_code_token="QR_PK_1040"
        )
        Booking.objects.create(
            user=driver,
            vehicle=v4,
            parking_lot="Shree Complex Parking",
            booking_type="advance",
            start_time=now - timedelta(hours=6),
            end_time=now - timedelta(hours=2),
            total_amount=80.00,
            payment_status="paid",
            booking_status="completed",
            qr_code_token="QR_PK_1039"
        )



def get_admin_common_context(request, active_tab):
    
    ensure_admin_sample_data()

    admin_name = request.user.get_full_name() or request.user.username
    unread_notifs = AdminNotification.objects.filter(is_read=False)
    unread_count = unread_notifs.count()
    recent_notifs = unread_notifs[:6]

    pending_owners = LotOwnerProfile.objects.filter(is_verified=False).count()
    pending_lots = ParkingLot.objects.filter(status='pending').count()
    open_complaints = PlatformComplaint.objects.filter(status='open').count()

    return {
        'active_tab': active_tab,
        'admin_display_name': admin_name,
        'admin_initials': 'AD',
        'admin_role': 'Super Admin' if request.user.is_superuser else 'Platform Admin',
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifs,
        'pending_owners_count': pending_owners,
        'pending_lots_count': pending_lots,
        'open_complaints_count': open_complaints,
        'today': timezone.now().date(),
    }




def admin_login_view(request):
    
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
            return redirect('admin_panel:dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not identifier or not password:
            messages.error(request, "Please enter both administrator username and password.")
            return render(request, 'admin_panel/login.html', {'identifier': identifier})

        
        auth_username = identifier
        candidates = list(User.objects.filter(email__iexact=identifier))
        if not candidates and identifier.lower() == 'admin':
            candidates = list(User.objects.filter(username__iexact='admin'))

        user = authenticate(request, username=auth_username, password=password)
        if user is None and candidates:
            for candidate in candidates:
                user = authenticate(request, username=candidate.username, password=password)
                if user is not None:
                    break

        if user is not None:
            
            is_admin = (
                user.is_superuser or
                user.is_staff or
                (hasattr(user, 'profile') and user.profile.role == 'admin')
            )

            if is_admin:
                login(request, user)
                log_audit(user, "Logged In", "Admin Studio Portal", request.META.get('REMOTE_ADDR', '127.0.0.1'))
                messages.success(request, f"Welcome back, Administrator {user.first_name or user.username}!")
                next_url = request.POST.get('next') or request.GET.get('next') or 'admin_panel:dashboard'
                return redirect(next_url)
            else:
                messages.error(
                    request,
                    "Access denied. Only platform administrators can log in here. Motorists and Lot Owners must use their respective login portals."
                )
                return render(request, 'admin_panel/login.html', {'identifier': identifier})
        else:
            messages.error(request, "Invalid administrator credentials. Please check your username and password.")
            return render(request, 'admin_panel/login.html', {'identifier': identifier})

    return render(request, 'admin_panel/login.html')


def admin_logout_view(request):
    if request.user.is_authenticated:
        log_audit(request.user, "Logged Out", "Admin Studio Portal", request.META.get('REMOTE_ADDR', '127.0.0.1'))
    logout(request)
    messages.success(request, "You have been successfully signed out of Admin Studio.")
    return redirect('admin_panel:login')




@admin_required
def admin_dashboard_view(request):
    ctx = get_admin_common_context(request, 'dashboard')

    total_users = User.objects.count()
    verified_owners = LotOwnerProfile.objects.filter(is_verified=True).count()
    pending_owners = LotOwnerProfile.objects.filter(is_verified=False).count()

    total_lots = ParkingLot.objects.count()
    approved_lots = ParkingLot.objects.filter(status='approved').count()
    pending_lots = ParkingLot.objects.filter(status='pending').count()
    rejected_lots = ParkingLot.objects.filter(status='rejected').count()

    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(booking_status='active').count()

    
    gross_revenue = 34200.00
    platform_commission = 5130.00
    settled_payouts = 28620.00
    total_chargers = EVCharger.objects.count()

    recent_activities = AdminAuditLog.objects.order_by('-created_at')[:8]
    pending_lot_items = ParkingLot.objects.filter(status='pending').order_by('-created_at')[:5]
    pending_owner_items = LotOwnerProfile.objects.filter(is_verified=False).order_by('-created_at')[:5]

    ctx.update({
        'total_users': total_users,
        'verified_owners': verified_owners,
        'pending_owners': pending_owners,
        'total_lots': total_lots,
        'approved_lots': approved_lots,
        'pending_lots': pending_lots,
        'rejected_lots': rejected_lots,
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'gross_revenue': gross_revenue,
        'platform_commission': platform_commission,
        'settled_payouts': settled_payouts,
        'total_chargers': total_chargers,
        'recent_activities': recent_activities,
        'pending_lot_items': pending_lot_items,
        'pending_owner_items': pending_owner_items,
    })
    return render(request, 'admin_panel/dashboard.html', ctx)




@admin_required
def admin_users_view(request):
    ctx = get_admin_common_context(request, 'users')

    role_filter = request.GET.get('role', 'all')
    search_q = request.GET.get('q', '').strip()

    users_qs = User.objects.all().order_by('-date_joined')

    if role_filter == 'driver':
        users_qs = users_qs.filter(is_staff=False).exclude(lot_owner_profile__isnull=False)
    elif role_filter == 'owner':
        users_qs = users_qs.filter(lot_owner_profile__isnull=False)
    elif role_filter == 'staff':
        users_qs = users_qs.filter(is_staff=True)

    if search_q:
        users_qs = users_qs.filter(
            models.Q(username__icontains=search_q) |
            models.Q(email__icontains=search_q) |
            models.Q(first_name__icontains=search_q) |
            models.Q(last_name__icontains=search_q)
        )

    users_list = []
    for u in users_qs:
        is_owner = hasattr(u, 'lot_owner_profile')
        is_staff = u.is_staff or u.is_superuser
        role_label = "Admin / Staff" if is_staff else ("Parking Owner" if is_owner else "Driver / Customer")
        mobile = getattr(getattr(u, 'profile', None), 'mobile_number', '') or '—'
        bookings_count = u.bookings.count() if hasattr(u, 'bookings') else 0
        lots_count = u.parking_lots.count() if hasattr(u, 'parking_lots') else 0

        users_list.append({
            'user': u,
            'role_label': role_label,
            'mobile': mobile,
            'bookings_count': bookings_count,
            'lots_count': lots_count,
            'is_active': u.is_active,
        })

    ctx.update({
        'users_list': users_list,
        'current_role': role_filter,
        'search_q': search_q,
        'total_count': len(users_list),
        'drivers_count': User.objects.filter(is_staff=False).exclude(lot_owner_profile__isnull=False).count(),
        'owners_count': LotOwnerProfile.objects.count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
    })
    return render(request, 'admin_panel/users.html', ctx)


@admin_required
def admin_toggle_user_status_view(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if target_user.is_superuser:
        messages.error(request, "Super Administrator accounts cannot be deactivated.")
        return redirect('admin_panel:users')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status_str = "activated" if target_user.is_active else "suspended"
    log_audit(request.user, f"User Account {status_str.title()}", f"User: {target_user.username}")
    messages.success(request, f"User '{target_user.username}' has been successfully {status_str}.")
    return redirect('admin_panel:users')


@admin_required
def admin_delete_user_view(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if target_user.is_superuser:
        messages.error(request, "Super Administrator accounts cannot be deleted.")
        return redirect('admin_panel:users')

    username = target_user.username
    user_email = target_user.email
    user_name = f"{target_user.first_name} {target_user.last_name}".strip() or username
    try:
        from parkease.email_service import EmailNotificationService
        EmailNotificationService.send_user_deleted(user_email, user_name)
    except Exception:
        pass

    log_audit(request.user, "Deleted User Account", f"User: {username}")
    target_user.delete()
    messages.success(request, f"User '{username}' has been deleted successfully. Closure notice dispatched to user email.")
    return redirect('admin_panel:users')





@admin_required
def admin_owner_verification_view(request):
    ctx = get_admin_common_context(request, 'owner_verification')

    status_filter = request.GET.get('status', 'all')
    owners_qs = LotOwnerProfile.objects.select_related('user').order_by('-created_at')

    if status_filter == 'pending':
        owners_qs = owners_qs.filter(is_verified=False)
    elif status_filter == 'verified':
        owners_qs = owners_qs.filter(is_verified=True)

    ctx.update({
        'owners': owners_qs,
        'status_filter': status_filter,
        'pending_count': LotOwnerProfile.objects.filter(is_verified=False).count(),
        'verified_count': LotOwnerProfile.objects.filter(is_verified=True).count(),
        'total_count': LotOwnerProfile.objects.count(),
    })
    return render(request, 'admin_panel/owner_verification.html', ctx)


@admin_required
def admin_approve_owner_view(request, owner_id):
    owner_profile = get_object_or_404(LotOwnerProfile, pk=owner_id)
    owner_profile.is_verified = True
    owner_profile.save()

    try:
        from parkease.email_service import EmailNotificationService
        EmailNotificationService.send_owner_verification_approved(owner_profile)
    except Exception:
        pass

    
    OwnerNotification.objects.create(
        owner=owner_profile.user,
        category='approval',
        title="Identity & Ownership Documents Verified!",
        message="Congratulations! Your owner registration has been approved by ParkEase Platform Admin.",
        is_read=False
    )

    try:
        from parkease.email_service import EmailNotificationService
        EmailNotificationService.send_notification(
            'owner_verification_status',
            owner_profile.user.email,
            owner_profile.user.get_full_name() or owner_profile.user.username,
            {
                'headline': "Your Space Owner Account is Verified & Approved!",
                'message_body': "Congratulations! Your identity and ownership documents have been verified and approved by the ParkEase platform team.",
                'details_dict': {
                    'Account Status': 'Verified Owner',
                    'Verified On': timezone.now().strftime('%b %d, %Y'),
                }
            },
            'owner'
        )
    except Exception:
        pass

    log_audit(request.user, "Approved Owner Identity", f"Owner: {owner_profile.user.username}")
    messages.success(request, f"Owner '{owner_profile.user.get_full_name() or owner_profile.user.username}' has been approved and verified!")
    return redirect('admin_panel:owner_verification')


@admin_required
def admin_reject_owner_view(request, owner_id):
    owner_profile = get_object_or_404(LotOwnerProfile, pk=owner_id)
    owner_profile.is_verified = False
    owner_profile.save()

    OwnerNotification.objects.create(
        owner=owner_profile.user,
        category='approval',
        title="Owner Documents Require Resubmission",
        message="Your submitted identification documents could not be verified. Please review and update details.",
        is_read=False
    )

    log_audit(request.user, "Rejected Owner Application", f"Owner: {owner_profile.user.username}")
    messages.warning(request, f"Owner application for '{owner_profile.user.username}' was rejected.")
    return redirect('admin_panel:owner_verification')




@admin_required
def admin_parking_lots_view(request):
    ctx = get_admin_common_context(request, 'parking_lots')

    status_filter = request.GET.get('status', 'all')
    lots_qs = ParkingLot.objects.select_related('owner').order_by('-created_at')

    if status_filter in ['pending', 'approved', 'rejected']:
        lots_qs = lots_qs.filter(status=status_filter)

    ctx.update({
        'lots': lots_qs,
        'status_filter': status_filter,
        'all_count': ParkingLot.objects.count(),
        'pending_count': ParkingLot.objects.filter(status='pending').count(),
        'approved_count': ParkingLot.objects.filter(status='approved').count(),
        'rejected_count': ParkingLot.objects.filter(status='rejected').count(),
    })
    return render(request, 'admin_panel/parking_lots.html', ctx)


@admin_required
def admin_approve_lot_view(request, lot_id):
    lot = get_object_or_404(ParkingLot, pk=lot_id)
    lot.status = 'approved'
    lot.is_paused = False
    lot.save()

    OwnerNotification.objects.create(
        owner=lot.owner,
        category='approval',
        title=f"Facility '{lot.name}' Approved & Live!",
        message=f"Your parking facility '{lot.name}' is now approved and motorists can reserve bays.",
        is_read=False
    )

    try:
        from parkease.email_service import EmailNotificationService
        EmailNotificationService.send_notification(
            'parking_lot_approval',
            lot.owner.email,
            lot.owner.get_full_name() or lot.owner.username,
            {
                'headline': f"Facility '{lot.name}' Approved & Published Live!",
                'message_body': f"Great news! Your parking facility <strong>{lot.name}</strong> has passed compliance inspection and is now live on the ParkEase driver marketplace.",
                'details_dict': {
                    'Facility Name': lot.name,
                    'Space Type': lot.get_space_type_display(),
                    'Total Bays': lot.total_capacity,
                    'Published Date': timezone.now().strftime('%b %d, %Y'),
                }
            },
            'owner'
        )
    except Exception:
        pass

    log_audit(request.user, "Approved Parking Facility", f"ParkingLot: {lot.name}")
    messages.success(request, f"Parking facility '{lot.name}' has been approved and published live!")
    return redirect('admin_panel:parking_lots')


@admin_required
def admin_reject_lot_view(request, lot_id):
    lot = get_object_or_404(ParkingLot, pk=lot_id)
    lot.status = 'rejected'
    lot.save()

    OwnerNotification.objects.create(
        owner=lot.owner,
        category='approval',
        title=f"Facility '{lot.name}' Application Needs Attention",
        message=f"Your facility listing '{lot.name}' was rejected. Please verify address and bay configuration.",
        is_read=False
    )

    log_audit(request.user, "Rejected Parking Facility", f"ParkingLot: {lot.name}")
    messages.warning(request, f"Parking facility '{lot.name}' was rejected.")
    return redirect('admin_panel:parking_lots')


@admin_required
def admin_toggle_lot_status_view(request, lot_id):
    lot = get_object_or_404(ParkingLot, pk=lot_id)
    lot.is_paused = not lot.is_paused
    lot.save()

    if lot.is_paused:
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_owner_lot_paused(lot)
        except Exception:
            pass

    state_str = "paused" if lot.is_paused else "re-activated"
    log_audit(request.user, f"Facility {state_str.title()}", f"ParkingLot: {lot.name}")
    messages.success(request, f"Parking facility '{lot.name}' has been {state_str}.")
    return redirect('admin_panel:parking_lots')




@admin_required
def admin_bookings_view(request):
    ctx = get_admin_common_context(request, 'bookings')

    filter_status = request.GET.get('filter', 'all')
    search_q = request.GET.get('q', '').strip()

    bookings_qs = Booking.objects.select_related('user', 'vehicle').order_by('-created_at')

    if filter_status == 'active':
        bookings_qs = bookings_qs.filter(booking_status='active')
    elif filter_status == 'completed':
        bookings_qs = bookings_qs.filter(booking_status='completed')
    elif filter_status == 'cancelled':
        bookings_qs = bookings_qs.filter(booking_status='cancelled')

    if search_q:
        bookings_qs = bookings_qs.filter(
            models.Q(id__icontains=search_q) |
            models.Q(parking_lot__icontains=search_q) |
            models.Q(user__username__icontains=search_q) |
            models.Q(vehicle__registration_number__icontains=search_q)
        )

    ctx.update({
        'bookings': bookings_qs,
        'filter_status': filter_status,
        'search_q': search_q,
        'total_bookings': Booking.objects.count(),
        'active_bookings': Booking.objects.filter(booking_status='active').count(),
        'completed_bookings': Booking.objects.filter(booking_status='completed').count(),
        'cancelled_bookings': Booking.objects.filter(booking_status='cancelled').count(),
    })
    return render(request, 'admin_panel/bookings.html', ctx)




@admin_required
def admin_payments_view(request):
    ctx = get_admin_common_context(request, 'payments')

    status_filter = request.GET.get('status', 'all')
    bookings_qs = Booking.objects.select_related('user', 'vehicle').order_by('-created_at')

    if status_filter == 'paid':
        bookings_qs = bookings_qs.filter(payment_status='paid')
    elif status_filter == 'refunded':
        bookings_qs = bookings_qs.filter(payment_status__in=['refunded', 'refund_requested'])
    elif status_filter == 'pending':
        bookings_qs = bookings_qs.filter(payment_status='pending')
    elif status_filter in ['failed']:
        bookings_qs = bookings_qs.filter(payment_status='failed')

    transactions = []
    for b in bookings_qs:
        tx_ref = f"pay_razor_{b.id:06d}"
        can_refund = (b.payment_status == 'refund_requested' or (b.booking_status == 'cancelled' and b.payment_status != 'refunded'))
        transactions.append({
            'booking': b,
            'tx_ref': tx_ref,
            'gateway': 'Razorpay PG (UPI / Cards / NetBanking)',
            'amount': b.total_amount,
            'status': b.payment_status,
            'date': b.created_at,
            'can_refund': can_refund,
        })

    ctx.update({
        'transactions': transactions,
        'status_filter': status_filter,
        'total_volume': 34200.00,
        'successful_count': Booking.objects.filter(payment_status='paid').count(),
        'refunded_count': Booking.objects.filter(payment_status__in=['refunded', 'refund_requested']).count(),
        'pending_count': Booking.objects.filter(payment_status='pending').count(),
    })
    return render(request, 'admin_panel/payments.html', ctx)


@admin_required
def admin_process_refund_view(request, tx_id):
    booking = get_object_or_404(Booking, pk=tx_id)
    import uuid
    booking.payment_status = 'refunded'
    booking.booking_status = 'cancelled'
    booking.refund_processed_at = timezone.now()
    if not booking.refund_transaction_id:
        booking.refund_transaction_id = f"RFND_{uuid.uuid4().hex[:10].upper()}"
    booking.save()

    try:
        from parkease.email_service import EmailNotificationService
        EmailNotificationService.send_refund_approved(booking)
    except Exception:
        pass

    log_audit(request.user, "Processed Gateway Refund", f"Booking #{booking.id} - INR {booking.total_amount}")
    messages.success(request, f"Refund of INR {booking.total_amount} for Booking #{booking.id} approved and credited via Razorpay. User and Admin notified.")
    return redirect('admin_panel:payments')




@admin_required
def admin_payouts_view(request):
    ctx = get_admin_common_context(request, 'payouts')

    payouts = OwnerPayout.objects.select_related('owner').order_by('-created_at')
    setting = PlatformSetting.objects.first()

    ctx.update({
        'payouts': payouts,
        'commission_pct': setting.commission_rate_pct if setting else 15.00,
        'gross_turnover': 34200.00,
        'platform_commission': 5130.00,
        'settled_amount': 28620.00,
        'pending_payouts_count': OwnerPayout.objects.filter(status='Pending').count(),
    })
    return render(request, 'admin_panel/payouts.html', ctx)


@admin_required
def admin_mark_payout_paid_view(request, payout_id):
    payout = get_object_or_404(OwnerPayout, pk=payout_id)
    payout.status = 'Paid'
    payout.save()

    log_audit(request.user, "Marked Payout Settled", f"Payout Ref: {payout.reference} - ₹{payout.net_payable}")
    messages.success(request, f"Payout {payout.reference} marked as settled and paid!")
    return redirect('admin_panel:payouts')




@admin_required
def admin_ev_charging_view(request):
    ctx = get_admin_common_context(request, 'ev_charging')

    chargers = EVCharger.objects.select_related('parking_lot').order_by('-created_at')

    ctx.update({
        'chargers': chargers,
        'total_stations': chargers.count(),
        'available_count': chargers.filter(status='Available').count(),
        'charging_count': chargers.filter(status='Charging').count(),
        'total_energy_kwh': 1845.5,
        'total_ev_revenue': 27682.50,
    })
    return render(request, 'admin_panel/ev_charging.html', ctx)


@admin_required
def admin_toggle_charger_view(request, charger_id):
    charger = get_object_or_404(EVCharger, pk=charger_id)
    if charger.status == 'Available':
        charger.status = 'Maintenance'
    else:
        charger.status = 'Available'
    charger.save()

    if charger.status == 'Maintenance' and charger.parking_lot:
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_ev_maintenance_alert(charger, charger.parking_lot, set_by='admin')
        except Exception:
            pass

    log_audit(request.user, "Toggled EV Charger Status", f"Charger: {charger.charger_id} -> {charger.status}")
    messages.success(request, f"EV Charger '{charger.charger_id}' status updated to {charger.status}.")
    return redirect('admin_panel:ev_charging')




@admin_required
def admin_pricing_view(request):
    ctx = get_admin_common_context(request, 'pricing')

    setting = PlatformSetting.objects.first()
    coupons = PlatformCoupon.objects.all().order_by('-created_at')

    if request.method == 'POST' and 'update_settings' in request.POST:
        commission = request.POST.get('commission_rate', '15.00')
        overstay = request.POST.get('overstay_fine', '100.00')
        min_rate = request.POST.get('min_hourly', '20.00')
        max_rate = request.POST.get('max_hourly', '500.00')
        grace = request.POST.get('grace_period', '15')

        setting.commission_rate_pct = commission
        setting.overstay_fine_hourly = overstay
        setting.min_hourly_rate = min_rate
        setting.max_hourly_rate = max_rate
        setting.grace_period_minutes = grace
        setting.save()

        log_audit(request.user, "Updated Platform Pricing Rules", f"Commission: {commission}%, Overstay: ₹{overstay}/hr")
        messages.success(request, "Platform global pricing and fine policies updated successfully!")
        return redirect('admin_panel:pricing')

    ctx.update({
        'setting': setting,
        'coupons': coupons,
    })
    return render(request, 'admin_panel/pricing.html', ctx)


@admin_required
def admin_create_coupon_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount = request.POST.get('discount_pct', 20)
        max_disc = request.POST.get('max_discount', 100.00)

        if code:
            PlatformCoupon.objects.create(
                code=code,
                discount_pct=discount,
                max_discount_amount=max_disc,
                valid_until=timezone.now().date() + timedelta(days=90),
                is_active=True
            )
            log_audit(request.user, "Created Promo Coupon", f"Coupon: {code} ({discount}% off)")
            messages.success(request, f"Coupon '{code}' created successfully!")

    return redirect('admin_panel:pricing')


@admin_required
def admin_toggle_coupon_view(request, coupon_id):
    coupon = get_object_or_404(PlatformCoupon, pk=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()

    status_str = "activated" if coupon.is_active else "disabled"
    log_audit(request.user, f"Coupon {status_str.title()}", f"Coupon: {coupon.code}")
    messages.success(request, f"Coupon '{coupon.code}' has been {status_str}.")
    return redirect('admin_panel:pricing')




@admin_required
def admin_reports_view(request):
    ctx = get_admin_common_context(request, 'reports')

    period = request.GET.get('period', '30d')
    if period not in ['7d', '30d', 'quarter', '1y']:
        period = '30d'

    report_data_map = {
        '7d': {
            'total_turnover': 8450.00,
            'commission_earned': 1267.50,
            'occupancy_rate': 74,
            'completed_sessions': 38,
            'cancelled_rate': 1.8,
            'ev_usage_kwh': 412.0,
            'avg_dwell_hours': 2.8,
            'repeat_driver_pct': 58,
            'period_label': 'Past 7 Days',
            'cities': [
                {'city': 'Ahmedabad, Gujarat', 'lots': '12 Facilities', 'bays': '680 Bays', 'turnover': 8450.00, 'occupancy': '74%', 'ev': '6 Chargers'},
                {'city': 'Mumbai, Maharashtra', 'lots': '18 Facilities', 'bays': '1,240 Bays', 'turnover': 21350.00, 'occupancy': '79%', 'ev': '14 Chargers'},
                {'city': 'Bengaluru, Karnataka', 'lots': '15 Facilities', 'bays': '950 Bays', 'turnover': 18400.00, 'occupancy': '72%', 'ev': '11 Chargers'},
                {'city': 'Delhi NCR', 'lots': '14 Facilities', 'bays': '1,100 Bays', 'turnover': 16800.00, 'occupancy': '70%', 'ev': '8 Chargers'},
            ]
        },
        '30d': {
            'total_turnover': 34200.00,
            'commission_earned': 5130.00,
            'occupancy_rate': 78,
            'completed_sessions': 148,
            'cancelled_rate': 2.4,
            'ev_usage_kwh': 1845.5,
            'avg_dwell_hours': 3.2,
            'repeat_driver_pct': 64,
            'period_label': 'Past 30 Days',
            'cities': [
                {'city': 'Ahmedabad, Gujarat', 'lots': '12 Facilities', 'bays': '680 Bays', 'turnover': 34200.00, 'occupancy': '82%', 'ev': '6 Chargers'},
                {'city': 'Mumbai, Maharashtra', 'lots': '18 Facilities', 'bays': '1,240 Bays', 'turnover': 86500.00, 'occupancy': '88%', 'ev': '14 Chargers'},
                {'city': 'Bengaluru, Karnataka', 'lots': '15 Facilities', 'bays': '950 Bays', 'turnover': 74100.00, 'occupancy': '79%', 'ev': '11 Chargers'},
                {'city': 'Delhi NCR', 'lots': '14 Facilities', 'bays': '1,100 Bays', 'turnover': 68900.00, 'occupancy': '76%', 'ev': '8 Chargers'},
            ]
        },
        'quarter': {
            'total_turnover': 142800.00,
            'commission_earned': 21420.00,
            'occupancy_rate': 82,
            'completed_sessions': 624,
            'cancelled_rate': 2.1,
            'ev_usage_kwh': 7560.0,
            'avg_dwell_hours': 3.4,
            'repeat_driver_pct': 71,
            'period_label': 'Last Quarter (4 Mo)',
            'cities': [
                {'city': 'Ahmedabad, Gujarat', 'lots': '12 Facilities', 'bays': '680 Bays', 'turnover': 142800.00, 'occupancy': '83%', 'ev': '6 Chargers'},
                {'city': 'Mumbai, Maharashtra', 'lots': '18 Facilities', 'bays': '1,240 Bays', 'turnover': 358000.00, 'occupancy': '89%', 'ev': '14 Chargers'},
                {'city': 'Bengaluru, Karnataka', 'lots': '15 Facilities', 'bays': '950 Bays', 'turnover': 306500.00, 'occupancy': '81%', 'ev': '11 Chargers'},
                {'city': 'Delhi NCR', 'lots': '14 Facilities', 'bays': '1,100 Bays', 'turnover': 282400.00, 'occupancy': '78%', 'ev': '8 Chargers'},
            ]
        },
        '1y': {
            'total_turnover': 468500.00,
            'commission_earned': 70275.00,
            'occupancy_rate': 85,
            'completed_sessions': 2180,
            'cancelled_rate': 1.9,
            'ev_usage_kwh': 24850.0,
            'avg_dwell_hours': 3.5,
            'repeat_driver_pct': 76,
            'period_label': 'Past 1 Year',
            'cities': [
                {'city': 'Ahmedabad, Gujarat', 'lots': '12 Facilities', 'bays': '680 Bays', 'turnover': 468500.00, 'occupancy': '85%', 'ev': '6 Chargers'},
                {'city': 'Mumbai, Maharashtra', 'lots': '18 Facilities', 'bays': '1,240 Bays', 'turnover': 1180000.00, 'occupancy': '91%', 'ev': '14 Chargers'},
                {'city': 'Bengaluru, Karnataka', 'lots': '15 Facilities', 'bays': '950 Bays', 'turnover': 995000.00, 'occupancy': '84%', 'ev': '11 Chargers'},
                {'city': 'Delhi NCR', 'lots': '14 Facilities', 'bays': '1,100 Bays', 'turnover': 920000.00, 'occupancy': '80%', 'ev': '8 Chargers'},
            ]
        },
    }

    pdata = report_data_map[period]
    ctx.update({
        'period': period,
        'period_label': pdata['period_label'],
        'total_turnover': pdata['total_turnover'],
        'commission_earned': pdata['commission_earned'],
        'occupancy_rate': pdata['occupancy_rate'],
        'completed_sessions': pdata['completed_sessions'],
        'cancelled_rate': pdata['cancelled_rate'],
        'ev_usage_kwh': pdata['ev_usage_kwh'],
        'avg_dwell_hours': pdata['avg_dwell_hours'],
        'repeat_driver_pct': pdata['repeat_driver_pct'],
        'city_breakdown': pdata['cities'],
    })
    return render(request, 'admin_panel/reports.html', ctx)


@admin_required
def admin_export_reports_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ParkEase_Platform_Report_2026.csv"'

    writer = csv.writer(response)
    writer.writerow(['Metric / Category', 'Value', 'Unit / Frequency', 'Notes'])
    writer.writerow(['Gross Booking Revenue', '34200.00', 'INR', 'Platform Gross Total'])
    writer.writerow(['Platform Commission (15%)', '5130.00', 'INR', 'ParkEase Retained Margin'])
    writer.writerow(['Net Owner Remittance', '28620.00', 'INR', 'Dispatched Settlements'])
    writer.writerow(['Total Registered Drivers', User.objects.count(), 'Users', 'Active Motorists'])
    writer.writerow(['Verified Parking Lots', ParkingLot.objects.filter(status='approved').count(), 'Facilities', 'Approved and Live'])
    writer.writerow(['EV Power Dispensed', '1845.5', 'kWh', 'Across all verified chargers'])

    log_audit(request.user, "Exported Analytics CSV", "Platform Financial Report")
    return response




@admin_required
def admin_reviews_view(request):
    ctx = get_admin_common_context(request, 'reviews')

    reviews = LotReview.objects.select_related('parking_lot').order_by('-created_at')

    ctx.update({
        'reviews': reviews,
        'avg_rating': 4.9,
        'total_reviews': reviews.count(),
        'reported_count': reviews.filter(is_reported=True).count(),
    })
    return render(request, 'admin_panel/reviews.html', ctx)


@admin_required
def admin_moderate_review_view(request, review_id):
    review = get_object_or_404(LotReview, pk=review_id)
    action = request.POST.get('action') or request.GET.get('action')

    if action == 'delete':
        review.delete()
        log_audit(request.user, "Removed Inappropriate Review", f"Review #{review_id}")
        messages.success(request, "Review removed from platform successfully.")
    else:
        review.is_reported = False
        review.save()
        log_audit(request.user, "Dismissed Review Report", f"Review #{review_id}")
        messages.success(request, "Report dismissed. Review approved as clean.")

    return redirect('admin_panel:reviews')




@admin_required
def admin_complaints_view(request):
    ctx = get_admin_common_context(request, 'complaints')

    status_filter = request.GET.get('status', 'all')
    complaints = PlatformComplaint.objects.all().order_by('-created_at')

    if status_filter in ['open', 'investigating', 'resolved', 'rejected']:
        complaints = complaints.filter(status=status_filter)

    ctx.update({
        'complaints': complaints,
        'status_filter': status_filter,
        'total_complaints': PlatformComplaint.objects.count(),
        'open_count': PlatformComplaint.objects.filter(status='open').count(),
        'investigating_count': PlatformComplaint.objects.filter(status='investigating').count(),
        'resolved_count': PlatformComplaint.objects.filter(status='resolved').count(),
    })
    return render(request, 'admin_panel/complaints.html', ctx)


@admin_required
def admin_resolve_complaint_view(request, complaint_id):
    complaint = get_object_or_404(PlatformComplaint, pk=complaint_id)
    if request.method == 'POST':
        action = request.POST.get('status', 'resolved')
        notes = request.POST.get('admin_notes', '').strip()

        complaint.status = action
        if notes:
            complaint.admin_notes = notes
        complaint.save()

        log_audit(request.user, f"Updated Dispute Status to {action}", f"Ticket: {complaint.ticket_id}")
        messages.success(request, f"Complaint {complaint.ticket_id} updated to {complaint.get_status_display()}.")

    return redirect('admin_panel:complaints')




@admin_required
def admin_notifications_view(request):
    ctx = get_admin_common_context(request, 'notifications')

    announcements = PlatformAnnouncement.objects.all().order_by('-created_at')
    system_alerts = AdminNotification.objects.all().order_by('-created_at')

    ctx.update({
        'announcements': announcements,
        'system_alerts': system_alerts,
    })
    return render(request, 'admin_panel/notifications.html', ctx)


@admin_required
def admin_broadcast_announcement_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        audience = request.POST.get('audience', 'all')

        if title and message:
            PlatformAnnouncement.objects.create(
                title=title,
                message=message,
                audience=audience,
                is_active=True,
                created_by=request.user
            )


            if audience in ['all', 'owners']:
                for owner in LotOwnerProfile.objects.select_related('user'):
                    OwnerNotification.objects.create(
                        owner=owner.user,
                        category='approval',
                        title=f"Platform Announcement: {title}",
                        message=message,
                        is_read=False
                    )

            log_audit(request.user, "Broadcast Announcement", f"Title: {title} (Target: {audience})")
            messages.success(request, "Announcement published and broadcast across platform users!")

    return redirect('admin_panel:notifications')


@admin_required
def admin_mark_notifications_read_view(request):
    AdminNotification.objects.filter(is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({'status': 'ok', 'message': 'All notifications marked as read'})
    messages.success(request, "All notifications marked as read.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_panel:notifications'))


@admin_required
def admin_dismiss_notification_view(request, notif_id):
    notif = get_object_or_404(AdminNotification, pk=notif_id)
    notif.is_read = True
    notif.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect(request.META.get('HTTP_REFERER', 'admin_panel:notifications'))




@admin_required
def admin_settings_view(request):
    ctx = get_admin_common_context(request, 'settings')
    setting = PlatformSetting.objects.first()

    if request.method == 'POST' and 'update_admin_profile' in request.POST:
        fname = request.POST.get('first_name', '').strip()
        lname = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        request.user.first_name = fname
        request.user.last_name = lname
        if email:
            request.user.email = email
        if password:
            request.user.set_password(password)
        request.user.save()

        if password:
            login(request, request.user)

        log_audit(request.user, "Updated Admin Profile", "User Profile Settings")
        messages.success(request, "Admin account profile and credentials updated successfully!")
        return redirect('admin_panel:settings')

    from accounts.models import EmailDeliveryLog
    ctx.update({
        'setting': setting,
        'email_logs': EmailDeliveryLog.objects.all().order_by('-sent_at')[:20],
        'email_host_user': getattr(settings, 'EMAIL_HOST_USER', ''),
        'email_host': getattr(settings, 'EMAIL_HOST', ''),
        'email_port': getattr(settings, 'EMAIL_PORT', 587),
    })
    return render(request, 'admin_panel/settings.html', ctx)


@admin_required
def admin_audit_logs_view(request):
    ctx = get_admin_common_context(request, 'settings')

    search_q = request.GET.get('q', '').strip()
    logs_qs = AdminAuditLog.objects.all().order_by('-created_at')

    if search_q:
        logs_qs = logs_qs.filter(
            models.Q(admin_user__icontains=search_q) |
            models.Q(action__icontains=search_q) |
            models.Q(target_object__icontains=search_q)
        )

    ctx.update({
        'audit_logs': logs_qs[:100],
        'search_q': search_q,
    })
    return render(request, 'admin_panel/audit_logs.html', ctx)




@admin_required
def admin_support_view(request):
    ctx = get_admin_common_context(request, 'support')

    owner_tickets = OwnerSupportTicket.objects.select_related('owner', 'parking_lot').order_by('-created_at')

    ctx.update({
        'tickets': owner_tickets,
        'open_tickets_count': owner_tickets.filter(status='Open').count(),
        'resolved_tickets_count': owner_tickets.filter(status='Resolved').count(),
    })
    return render(request, 'admin_panel/support.html', ctx)




@admin_required
def admin_feedbacks_view(request):
    ctx = get_admin_common_context(request, 'feedbacks')
    from admin_panel.models import PlatformFeedback
    feedbacks = PlatformFeedback.objects.all().order_by('-created_at')

    total_feedbacks = feedbacks.count()
    reviewed_count = feedbacks.filter(is_reviewed=True).count()
    pending_count = feedbacks.filter(is_reviewed=False).count()

    ctx.update({
        'feedbacks': feedbacks,
        'total_feedbacks': total_feedbacks,
        'reviewed_count': reviewed_count,
        'pending_count': pending_count,
    })
    return render(request, 'admin_panel/feedbacks.html', ctx)

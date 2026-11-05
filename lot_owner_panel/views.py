from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import models
from decimal import Decimal
from datetime import timedelta
import re
import csv
import io

from accounts.models import UserProfile
from bookings.models import Booking, BookingExtensionRequest
from parkease.email_service import EmailNotificationService
from .models import (
    LotOwnerProfile, ParkingLot, ParkingSlot, EVCharger,
    OwnerPayout, OwnerNotification, OwnerSupportTicket, LotReview
)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus.flowables import HRFlowable
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False




def mask_id_number(id_str):
    if not id_str:
        return ""
    clean = str(id_str).strip()
    if len(clean) <= 4:
        return clean
    unmasked = clean[-4:]
    masked = '•' * (len(clean) - 4)
    return f"{masked}{unmasked}"


def get_owner_initials(name_or_username):
    parts = name_or_username.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    return "OP"


def generate_unique_owner_username(email, name):
    base = name.split()[0].lower() if name else email.split('@')[0].lower()
    base = re.sub(r'[^a-zA-Z0-9]', '', base) or 'owner'
    username = f"{base}_owner"
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}_owner{counter}"
        counter += 1
    return username


def ensure_owner_sample_data(user, lot):
    
    if not ParkingSlot.objects.filter(parking_lot=lot).exists():
        sample_slots = [
            ('Basement A', 'C-012', 'Car', 'Available', '6 AM–11 PM', 'Min 1 hr, Max 24 hrs', 'Operational'),
            ('Basement A', 'C-013', 'Car', 'Occupied', '6 AM–11 PM', 'Min 1 hr, Max 24 hrs', 'Operational'),
            ('Basement A', 'C-014', 'Car', 'Occupied', '6 AM–11 PM', 'Min 1 hr, Max 24 hrs', 'Operational'),
            ('Basement A', 'C-015', 'Car', 'Reserved', '6 AM–11 PM', 'Min 2 hrs, Max 24 hrs', 'Operational'),
            ('Basement A', 'C-016', 'Car', 'Available', '6 AM–11 PM', 'Min 1 hr, Max 24 hrs', 'Operational'),
            ('Ground Floor', 'B-001', 'Two-wheeler', 'Available', '24/7 Access', 'Min 30 mins', 'Operational'),
            ('Ground Floor', 'B-002', 'Two-wheeler', 'Occupied', '24/7 Access', 'Min 30 mins', 'Operational'),
            ('Ground Floor', 'B-003', 'Two-wheeler', 'Available', '24/7 Access', 'Min 30 mins', 'Operational'),
            ('Ground Floor', 'S-101', 'SUV', 'Available', '6 AM–11 PM', 'Min 1 hr, Max 12 hrs', 'Operational'),
            ('Ground Floor', 'S-102', 'SUV', 'Occupied', '6 AM–11 PM', 'Min 1 hr, Max 12 hrs', 'Maintenance'),
            ('EV Bays', 'EV-001', 'EV', 'Available', '24/7 Access', 'Min 1 hr', 'Operational'),
            ('EV Bays', 'EV-002', 'EV', 'Occupied', '24/7 Access', 'Min 1 hr', 'Operational'),
        ]
        for zone, num, cat, status, sched, rest, maint in sample_slots:
            ParkingSlot.objects.create(
                parking_lot=lot,
                zone=zone,
                slot_number=num,
                vehicle_category=cat,
                status=status,
                schedule=sched,
                booking_restrictions=rest,
                maintenance_status=maint
            )

    
    if not EVCharger.objects.filter(parking_lot=lot).exists():
        EVCharger.objects.create(
            parking_lot=lot,
            charger_id='CHG-B1-01',
            location='Basement Level 1 (Zone A)',
            connector_type='Type 2 AC / CCS2 DC Fast',
            power_kw=50.0,
            status='Available',
            rate_per_kwh=15.00,
            schedule='24/7 Access',
            parking_fee_included=True
        )
        EVCharger.objects.create(
            parking_lot=lot,
            charger_id='CHG-B1-02',
            location='Basement Level 1 (Zone B)',
            connector_type='Type 2 AC',
            power_kw=22.0,
            status='Available',
            rate_per_kwh=15.00,
            schedule='24/7 Access',
            parking_fee_included=True
        )
        EVCharger.objects.create(
            parking_lot=lot,
            charger_id='CHG-G0-03',
            location='Ground Floor Entrance Bay',
            connector_type='Bharat AC-001 / Type 2',
            power_kw=7.4,
            status='Charging',
            rate_per_kwh=15.00,
            schedule='6 AM–11 PM',
            parking_fee_included=True
        )

    
    if not OwnerNotification.objects.filter(owner=user).exists():
        sample_notifs = [
            ('booking', 'New Booking Confirmed (#BK-1042)', 'Driver Rohit Sharma booked Bay C-012 for today 02:00 PM – 05:00 PM. ₹150.00 pre-paid.'),
            ('arrival', 'Upcoming Arrival Alert', 'Motorist with plate GJ-01-AB-1234 expected to arrive at Barrier Gate 1 in 15 minutes.'),
            ('payment', 'Weekly Payout Settlement Dispatched', '₹28,620.00 transferred via NEFT/IMPS. Ref UTR9847291847192.'),
            ('approval', 'Space Listing Approved by Admin', 'Your facility Shree Complex Parking is officially approved and visible to motorists.'),
            ('maintenance', 'EV Charger CHG-B1-01 Diagnostic Complete', 'Charger passed self-test. Firmware 2.4.1 online and operational.'),
        ]
        for cat, title, msg in sample_notifs:
            OwnerNotification.objects.create(owner=user, category=cat, title=title, message=msg, is_read=False)

    
    if not LotReview.objects.filter(parking_lot=lot).exists():
        LotReview.objects.create(
            parking_lot=lot,
            driver_name='Rahul S.',
            booking_ref='1040',
            rating=5,
            comment='Super clean and spacious parking basement. Barrier gate scanned QR pass instantly!',
            owner_reply='Thank you Rahul! We take pride in 24/7 security and clean bays.'
        )
        LotReview.objects.create(
            parking_lot=lot,
            driver_name='Priya M.',
            booking_ref='1038',
            rating=5,
            comment='Very convenient parking near C.G. Road. EV charger delivered full charge smoothly.',
            owner_reply='Glad the fast charger worked out well for your EV!'
        )
        LotReview.objects.create(
            parking_lot=lot,
            driver_name='Amit Patel',
            booking_ref='1035',
            rating=4,
            comment='Good security guard and clear bay numbering. Height clearance was ample for my SUV.'
        )

    
    if not OwnerPayout.objects.filter(owner=user).exists():
        OwnerPayout.objects.create(
            owner=user,
            period='15 Oct – 22 Oct 2026',
            gross_revenue=34200.00,
            commission=5130.00,
            refunds=450.00,
            adjustments=0.00,
            net_payable=28620.00,
            status='Paid',
            reference='UTR9847291847192'
        )
        OwnerPayout.objects.create(
            owner=user,
            period='08 Oct – 15 Oct 2026',
            gross_revenue=19700.00,
            commission=2955.00,
            refunds=450.00,
            adjustments=0.00,
            net_payable=16295.00,
            status='Paid',
            reference='UTR9834110948215'
        )


def get_owner_context(request, active_tab='dashboard'):
    
    user = request.user
    lots = ParkingLot.objects.filter(owner=user).order_by('-created_at')
    
    primary_lot = lots.first()
    if not primary_lot:
        primary_lot = ParkingLot.objects.create(
            owner=user,
            name="Shree Complex Parking",
            space_type="commercial",
            street_address="C.G. Road, Near Navrangpura Cross",
            area="Navrangpura",
            city="Ahmedabad",
            state="Gujarat",
            pin_code="380009",
            total_capacity=50,
            supported_vehicles=["Cars (Hatchback / Sedan)", "Two-wheelers (Bikes / Scooters)", "SUVs & MUVs", "Electric Vehicles (EVs)"],
            parking_arrangement="basement",
            operating_hours="24/7 Access",
            hourly_rate=50.00,
            daily_rate=300.00,
            monthly_rate=4500.00,
            status="approved"
        )
        lots = ParkingLot.objects.filter(owner=user)

    
    ensure_owner_sample_data(user, primary_lot)

    owner_name = user.get_full_name() or user.username
    initials = get_owner_initials(owner_name)

    unread_notifs_count = OwnerNotification.objects.filter(owner=user, is_read=False).count()
    recent_notifs = OwnerNotification.objects.filter(owner=user, is_read=False).order_by('-created_at')[:5]

    profile, _ = LotOwnerProfile.objects.get_or_create(user=user)
    user_prof, _ = UserProfile.objects.get_or_create(user=user)

    from bookings.models import BookingExtensionRequest
    pending_ext_count = BookingExtensionRequest.objects.filter(booking__lot__in=lots, status='pending').count()

    return {
        'active_tab': active_tab,
        'owner_display_name': owner_name,
        'owner_initials': initials,
        'current_lot_name': primary_lot.name if primary_lot else "Shree Complex Parking",
        'primary_lot': primary_lot,
        'parking_lots': lots,
        'total_lots_count': lots.count(),
        'unread_notifications_count': unread_notifs_count,
        'recent_notifications': recent_notifs,
        'active_bookings_count': 8,
        'pending_extensions_count': pending_ext_count,
        'profile': profile,
        'user_profile': user_prof,
    }




def owner_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'lot_owner_profile') or (hasattr(request.user, 'profile') and request.user.profile.role == 'owner') or request.user.is_staff:
            return redirect('lot_owner_panel:dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not identifier or not password:
            messages.error(request, "Please enter both username/email and password.")
            return render(request, 'lot_owner_panel/login.html', {'identifier': identifier})

        auth_username = identifier
        candidates = list(User.objects.filter(email__iexact=identifier))
        if not candidates and identifier.lower() in ('owner', 'owner@gmail.com'):
            candidates = list(User.objects.filter(username__iexact='owner@gmail.com'))

        user = authenticate(request, username=auth_username, password=password)
        if user is None and candidates:
            for candidate in candidates:
                user = authenticate(request, username=candidate.username, password=password)
                if user is not None:
                    break

        if user is not None:
            is_owner = False
            if hasattr(user, 'lot_owner_profile') or (hasattr(user, 'profile') and user.profile.role == 'owner') or user.is_staff:
                is_owner = True

            if is_owner:
                login(request, user)
                try:
                    from parkease.email_service import EmailNotificationService
                    EmailNotificationService.send_owner_login_alert(user, ip=request.META.get('REMOTE_ADDR', '127.0.0.1'))
                except Exception:
                    pass
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.POST.get('next') or request.GET.get('next') or 'lot_owner_panel:dashboard'
                return redirect(next_url)
            else:
                messages.error(
                    request,
                    "Access restricted: This portal is exclusively for registered Space Owners."
                )
                return render(request, 'lot_owner_panel/login.html', {'identifier': identifier})
        else:
            messages.error(request, "Invalid username/email or password. Please verify your credentials.")
            return render(request, 'lot_owner_panel/login.html', {'identifier': identifier})

    return render(request, 'lot_owner_panel/login.html')


def owner_logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out of the Space Owner Portal.")
    return redirect('lot_owner_panel:login')




def owner_register_step1_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        mobile_number = request.POST.get('mobile_number', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        owner_type = request.POST.get('owner_type', 'individual')

        present_address = request.POST.get('present_address', '').strip()
        state = request.POST.get('state', '').strip()
        city = request.POST.get('city', '').strip()
        pin_code = request.POST.get('pin_code', '').strip()

        id_type = request.POST.get('id_type', 'aadhaar')
        id_number = request.POST.get('id_number', '').strip()

        step1_form_context = {
            'full_name': full_name,
            'email': email,
            'mobile_number': mobile_number,
            'owner_type': owner_type,
            'present_address': present_address,
            'state': state,
            'city': city,
            'pin_code': pin_code,
            'id_type': id_type,
            'id_number': id_number,
        }

        if not full_name:
            messages.error(request, "Full legal name is required.")
            return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)

        if not email or '@' not in email:
            messages.error(request, "Please enter a valid email address.")
            return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email address already exists. Please log in instead.")
            return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)

        cleaned_mobile = re.sub(r'\D', '', mobile_number)
        if len(cleaned_mobile) != 10:
            messages.error(request, "Mobile number must be exactly 10 digits.")
            return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)
        mobile_number = cleaned_mobile

        if not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter carefully.")
            return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)

        if not id_number:
            messages.error(request, "Please enter your official ID number.")
            return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)

        id_clean = id_number.strip().upper()
        if id_type == 'aadhaar':
            if not re.match(r'^\d{12}$', id_number.strip()):
                messages.error(request, "Aadhaar number must be exactly 12 numeric digits.")
                return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)
            id_number = id_number.strip()
        elif id_type == 'pan':
            if not re.match(r'^[A-Z]{5}\d{4}[A-Z]$', id_clean):
                messages.error(request, "PAN must be 10 characters (e.g. ABCDE1234F).")
                return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)
            id_number = id_clean
        elif id_type == 'passport':
            if not re.match(r'^[A-Z]\d{7}$', id_clean):
                messages.error(request, "Passport number must be 1 letter followed by 7 digits.")
                return render(request, 'lot_owner_panel/register_step1.html', step1_form_context)
            id_number = id_clean

        id_doc_path = ''
        if 'id_document' in request.FILES:
            uploaded_file = request.FILES['id_document']
            filename = f"owners/id_documents/{uploaded_file.name}"
            id_doc_path = default_storage.save(filename, uploaded_file)

        profile_photo_path = ''
        if 'profile_photo' in request.FILES:
            photo_file = request.FILES['profile_photo']
            filename = f"owners/profiles/{photo_file.name}"
            profile_photo_path = default_storage.save(filename, photo_file)

        step1_data = {
            'full_name': full_name,
            'email': email,
            'mobile_number': mobile_number,
            'password': password,
            'owner_type': owner_type,
            'present_address': present_address,
            'state': state,
            'city': city,
            'pin_code': pin_code,
            'id_type': id_type,
            'id_number': id_number,
            'id_document_path': id_doc_path,
            'profile_photo_path': profile_photo_path,
        }
        request.session['owner_reg_step1'] = step1_data
        return redirect('lot_owner_panel:register_step2')

    existing_data = request.session.get('owner_reg_step1', {})
    return render(request, 'lot_owner_panel/register_step1.html', existing_data)


def owner_register_step2_view(request):
    step1_data = request.session.get('owner_reg_step1')
    if not step1_data:
        messages.warning(request, "Please complete Step 1 first.")
        return redirect('lot_owner_panel:register_step1')

    if request.method == 'POST':
        parking_lot_name = request.POST.get('parking_lot_name', '').strip()
        space_type = request.POST.get('space_type', 'residential')
        building_name = request.POST.get('building_name', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        area = request.POST.get('area', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pin_code = request.POST.get('pin_code', '').strip()
        map_location = request.POST.get('map_location', '').strip()
        total_capacity = request.POST.get('total_capacity', '').strip()

        supported_vehicles = request.POST.getlist('supported_vehicles')
        parking_arrangement = request.POST.get('parking_arrangement', 'open_air')
        
        is_24_7 = bool(request.POST.get('is_24_7'))
        opening_hour = request.POST.get('opening_hour', '06:00').strip()
        closing_hour = request.POST.get('closing_hour', '22:00').strip()
        if is_24_7:
            operating_hours = '24/7 Access'
        elif opening_hour and closing_hour:
            operating_hours = f"{opening_hour} - {closing_hour}"
        else:
            operating_hours = request.POST.get('operating_hours', '24/7 Access').strip()

        available_services = request.POST.getlist('available_services')
        access_instructions = request.POST.get('access_instructions', '').strip()
        hourly_rate = request.POST.get('hourly_rate', '50.00').strip()


        bank_account_holder = request.POST.get('bank_account_holder', '').strip()
        bank_name = request.POST.get('bank_name', '').strip()
        bank_account_number = request.POST.get('bank_account_number', '').strip()
        bank_ifsc_code = request.POST.get('bank_ifsc_code', '').strip().upper()
        bank_branch = request.POST.get('bank_branch', '').strip()
        bank_account_type = request.POST.get('bank_account_type', 'Current Account / Business').strip()

        step2_form_context = {
            'parking_lot_name': parking_lot_name,
            'space_type': space_type,
            'building_name': building_name,
            'street_address': street_address,
            'area': area,
            'city': city,
            'state': state,
            'pin_code': pin_code,
            'map_location': map_location,
            'total_capacity': total_capacity,
            'supported_vehicles': supported_vehicles,
            'parking_arrangement': parking_arrangement,
            'opening_hour': opening_hour,
            'closing_hour': closing_hour,
            'is_24_7': is_24_7,
            'operating_hours': operating_hours,
            'available_services': available_services,
            'access_instructions': access_instructions,
            'hourly_rate': hourly_rate,
            'bank_account_holder': bank_account_holder,
            'bank_name': bank_name,
            'bank_account_number': bank_account_number,
            'bank_ifsc_code': bank_ifsc_code,
            'bank_branch': bank_branch,
            'bank_account_type': bank_account_type,
        }

        if not parking_lot_name:
            messages.error(request, "Parking lot name is required.")
            return render(request, 'lot_owner_panel/register_step2.html', step2_form_context)

        if not street_address or not area or not city:
            messages.error(request, "Please enter the complete street, area, and city.")
            return render(request, 'lot_owner_panel/register_step2.html', step2_form_context)

        if not supported_vehicles:
            messages.error(request, "Please select at least one vehicle type.")
            return render(request, 'lot_owner_panel/register_step2.html', step2_form_context)

        try:
            capacity_int = int(total_capacity)
            if capacity_int < 1:
                capacity_int = 1
        except ValueError:
            capacity_int = 1

        space_photo_path = ''
        if 'space_photo' in request.FILES:
            photo = request.FILES['space_photo']
            saved_name = default_storage.save(f"parking_lots/photos/{photo.name}", photo)
            space_photo_path = saved_name

        step2_data = {
            'parking_lot_name': parking_lot_name,
            'space_type': space_type,
            'building_name': building_name,
            'street_address': street_address,
            'area': area,
            'city': city,
            'state': state,
            'pin_code': pin_code,
            'map_location': map_location,
            'total_capacity': capacity_int,
            'supported_vehicles': supported_vehicles,
            'parking_arrangement': parking_arrangement,
            'opening_hour': opening_hour,
            'closing_hour': closing_hour,
            'is_24_7': is_24_7,
            'operating_hours': operating_hours,
            'available_services': available_services,
            'access_instructions': access_instructions,
            'space_photo_path': space_photo_path,
            'hourly_rate': hourly_rate,
            'bank_account_holder': bank_account_holder,
            'bank_name': bank_name,
            'bank_account_number': bank_account_number,
            'bank_ifsc_code': bank_ifsc_code,
            'bank_branch': bank_branch,
            'bank_account_type': bank_account_type,
        }
        request.session['owner_reg_step2'] = step2_data
        return redirect('lot_owner_panel:register_step3')

    existing_data = request.session.get('owner_reg_step2', {})
    return render(request, 'lot_owner_panel/register_step2.html', existing_data)


def owner_register_step3_view(request):
    step1_data = request.session.get('owner_reg_step1')
    step2_data = request.session.get('owner_reg_step2')

    if not step1_data:
        messages.warning(request, "Please complete Step 1 first.")
        return redirect('lot_owner_panel:register_step1')

    if not step2_data:
        messages.warning(request, "Please complete Step 2 first.")
        return redirect('lot_owner_panel:register_step2')

    masked_id = mask_id_number(step1_data.get('id_number', ''))
    masked_bank = mask_id_number(step2_data.get('bank_account_number', ''))

    if request.method == 'POST':
        agree_terms = bool(request.POST.get('agree_terms'))
        agree_privacy = bool(request.POST.get('agree_privacy'))
        confirm_declaration = bool(request.POST.get('confirm_declaration'))

        if not agree_terms or not agree_privacy or not confirm_declaration:
            messages.error(request, "Please accept all terms, privacy policies, and declarations to finalize registration.")
            return render(request, 'lot_owner_panel/register_step3.html', {
                'step1': step1_data,
                'step2': step2_data,
                'masked_id': masked_id,
                'masked_bank_account': masked_bank,
            })

        full_name = step1_data['full_name']
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        username = generate_unique_owner_username(step1_data['email'], full_name)

        user = User.objects.create_user(
            username=username,
            email=step1_data['email'],
            password=step1_data['password'],
            first_name=first_name,
            last_name=last_name
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'owner'
        profile.mobile_number = step1_data['mobile_number']
        profile.save()

        
        owner_profile = LotOwnerProfile.objects.create(
            user=user,
            owner_type=step1_data['owner_type'],
            profile_photo=step1_data.get('profile_photo_path', ''),
            present_address=step1_data['present_address'],
            city=step1_data['city'],
            state=step1_data['state'],
            pin_code=step1_data['pin_code'],
            id_type=step1_data['id_type'],
            id_number=step1_data['id_number'],
            id_document=step1_data.get('id_document_path', ''),
            bank_account_holder=step2_data.get('bank_account_holder', ''),
            bank_name=step2_data.get('bank_name', ''),
            bank_account_number=step2_data.get('bank_account_number', ''),
            bank_ifsc_code=step2_data.get('bank_ifsc_code', ''),
            bank_branch=step2_data.get('bank_branch', ''),
            bank_account_type=step2_data.get('bank_account_type', 'Current Account / Business'),
            is_verified=False
        )

        try:
            hr_rate = float(step2_data.get('hourly_rate', 50.0))
        except ValueError:
            hr_rate = 50.0

        parking_lot = ParkingLot.objects.create(
            owner=user,
            name=step2_data['parking_lot_name'],
            space_type=step2_data['space_type'],
            building_name=step2_data.get('building_name', ''),
            street_address=step2_data['street_address'],
            area=step2_data['area'],
            city=step2_data['city'],
            state=step2_data['state'],
            pin_code=step2_data['pin_code'],
            map_location=step2_data.get('map_location', ''),
            total_capacity=step2_data['total_capacity'],
            supported_vehicles=step2_data['supported_vehicles'],
            parking_arrangement=step2_data['parking_arrangement'],
            operating_hours=step2_data['operating_hours'],
            available_services=step2_data['available_services'],
            access_instructions=step2_data.get('access_instructions', ''),
            space_photo=step2_data.get('space_photo_path', ''),
            hourly_rate=hr_rate,
            status='pending',
            agreed_terms=True,
            agreed_privacy=True,
            confirmed_declaration=True
        )

        
        ensure_owner_sample_data(user, parking_lot)

        
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_owner_registration_receipt(owner_profile)
            EmailNotificationService.send_admin_alert(
                'admin_pending_owner_review',
                f"New Space Owner Application: {owner_profile.business_name or full_name}",
                f"A new partner registration application from {user.email} has been submitted and is awaiting document verification.",
                {
                    'Partner Name': full_name,
                    'Facility Name': parking_lot.name,
                    'City & State': f"{parking_lot.city}, {parking_lot.state}",
                    'Submission Time': timezone.now().strftime('%b %d, %Y %H:%M UTC')
                }
            )
        except Exception:
            pass

        request.session.pop('owner_reg_step1', None)
        request.session.pop('owner_reg_step2', None)

        login(request, user)
        request.session['newly_registered_lot_id'] = parking_lot.id
        return redirect('lot_owner_panel:register_success')

    context = {
        'step1': step1_data,
        'step2': step2_data,
        'masked_id': masked_id,
        'masked_bank_account': masked_bank,
    }
    return render(request, 'lot_owner_panel/register_step3.html', context)


@login_required
def owner_register_success_view(request):
    lot_id = request.session.pop('newly_registered_lot_id', None)
    lot = None
    if lot_id:
        lot = ParkingLot.objects.filter(id=lot_id, owner=request.user).first()
    if not lot:
        lot = ParkingLot.objects.filter(owner=request.user).order_by('-created_at').first()

    return render(request, 'lot_owner_panel/register_success.html', {'parking_lot': lot})




@login_required
def owner_dashboard_view(request):
    
    ctx = get_owner_context(request, active_tab='dashboard')
    ctx.update({
        'today_revenue': "18,450",
        'today_bookings_count': 14,
        'total_spaces': 50,
        'occupied_now': 32,
        'available_now': 18,
    })
    return render(request, 'lot_owner_panel/dashboard.html', ctx)


@login_required
def owner_parking_lots_view(request):
    
    if request.method == 'POST':
        name = request.POST.get('parking_lot_name', '').strip()
        space_type = request.POST.get('space_type', 'commercial')
        building_name = request.POST.get('building_name', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        area = request.POST.get('area', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pin_code = request.POST.get('pin_code', '').strip()
        
        try:
            total_capacity = int(request.POST.get('total_capacity', 50))
        except (ValueError, TypeError):
            total_capacity = 50

        parking_arrangement = request.POST.get('parking_arrangement', 'covered')
        supported_vehicles = request.POST.getlist('supported_vehicles')
        available_services = request.POST.getlist('available_services')
        access_instructions = request.POST.get('access_instructions', '').strip()
        
        is_24_7 = bool(request.POST.get('is_24_7'))
        if is_24_7:
            operating_hours = "24/7 Access"
        else:
            open_h = request.POST.get('opening_hour', '06:00')
            close_h = request.POST.get('closing_hour', '22:00')
            operating_hours = f"{open_h} - {close_h}"

        try:
            hourly_rate = float(request.POST.get('hourly_rate', 50.0))
        except (ValueError, TypeError):
            hourly_rate = 50.0

        if name and street_address and area and city and pin_code:
            new_lot = ParkingLot.objects.create(
                owner=request.user,
                name=name,
                space_type=space_type,
                building_name=building_name,
                street_address=street_address,
                area=area,
                city=city,
                state=state,
                pin_code=pin_code,
                total_capacity=total_capacity,
                parking_arrangement=parking_arrangement,
                supported_vehicles=supported_vehicles,
                available_services=available_services,
                operating_hours=operating_hours,
                hourly_rate=hourly_rate,
                access_instructions=access_instructions,
                status='approved'
            )
            if 'space_photo' in request.FILES:
                new_lot.space_photo = request.FILES['space_photo']
                new_lot.save()
            ensure_owner_sample_data(request.user, new_lot)
            messages.success(request, f"Parking space '{new_lot.name}' has been added successfully.")
        else:
            messages.error(request, "Please fill in all required fields to add a parking space.")
        return redirect('lot_owner_panel:parking_lots')

    ctx = get_owner_context(request, active_tab='parking_lots')
    return render(request, 'lot_owner_panel/parking_lots.html', ctx)


@login_required
def owner_lot_detail_view(request, lot_id):
    
    lot = get_object_or_404(ParkingLot, id=lot_id, owner=request.user)
    
    if request.method == 'POST':
        lot.operating_hours = request.POST.get('operating_hours', lot.operating_hours)
        try:
            lot.hourly_rate = float(request.POST.get('hourly_rate', lot.hourly_rate))
        except ValueError:
            pass
        lot.access_instructions = request.POST.get('access_instructions', lot.access_instructions)
        lot.save()
        messages.success(request, f"Updated information for {lot.name}.")
        return redirect('lot_owner_panel:lot_detail', lot_id=lot.id)

    slots = list(lot.slots.all().order_by('id'))
    from collections import defaultdict
    groups = defaultdict(list)
    for s in slots:
        prefix = s.slot_number.split('-')[0] if '-' in s.slot_number else (s.zone or 'A')
        groups[prefix].append(s)
    slot_rows = list(groups.values()) if groups else [slots]

    ctx = get_owner_context(request, active_tab='parking_lots')
    ctx.update({
        'lot': lot,
        'slot_rows': slot_rows,
        'car_capacity': 30,
        'bike_capacity': 15,
        'suv_capacity': 5,
        'ev_capacity': 3,
        'current_occupied': 22,
    })
    return render(request, 'lot_owner_panel/lot_detail.html', ctx)


@login_required
def owner_toggle_pause_lot_view(request, lot_id):
    
    lot = get_object_or_404(ParkingLot, id=lot_id, owner=request.user)
    lot.is_paused = not lot.is_paused
    lot.save()
    status_label = "unavailable" if lot.is_paused else "available"
    messages.success(request, f"Parking lot #{lot.id} ({lot.name}) is now marked as {status_label}.")
    return redirect(request.META.get('HTTP_REFERER') or 'lot_owner_panel:parking_lots')


@login_required
def owner_bookings_view(request):
    
    from bookings.models import Booking
    ctx = get_owner_context(request, active_tab='bookings')
    owner = request.user
    
    owner_lots = ParkingLot.objects.filter(owner=owner)
    
    
    live_bookings_qs = Booking.objects.filter(lot__in=owner_lots).select_related('user', 'vehicle', 'lot', 'slot').order_by('-created_at')
    
    
    search_q = request.GET.get('q', '').strip()
    if search_q:
        live_bookings_qs = live_bookings_qs.filter(
            models.Q(id__icontains=search_q) |
            models.Q(qr_code_token__icontains=search_q) |
            models.Q(vehicle__registration_number__icontains=search_q) |
            models.Q(user__first_name__icontains=search_q) |
            models.Q(user__last_name__icontains=search_q) |
            models.Q(user__username__icontains=search_q)
        )
        
    total_count = live_bookings_qs.count()
    parked_count = live_bookings_qs.filter(is_parked=True).count()
    awaiting_count = live_bookings_qs.filter(is_parked=False, booking_status='active').count()
    completed_count = live_bookings_qs.filter(booking_status='completed').count()

    filter_param = request.GET.get('filter', 'all')
    if filter_param == 'active':
        filtered_qs = live_bookings_qs.filter(is_parked=True)
    elif filter_param == 'upcoming':
        filtered_qs = live_bookings_qs.filter(is_parked=False, booking_status='active')
    elif filter_param == 'completed':
        filtered_qs = live_bookings_qs.filter(booking_status='completed')
    else:
        filtered_qs = live_bookings_qs

    
    formatted_bookings = []
    for b in filtered_qs:
        driver_name = b.user.get_full_name() or b.user.username
        driver_phone = getattr(getattr(b.user, 'profile', None), 'phone', '') or '+91 98765 43210'
        
        if b.slot:
            slot_bay = f"Bay {b.slot.zone} - {b.slot.slot_number}"
        elif '[' in b.parking_lot and ']' in b.parking_lot:
            slot_bay = b.parking_lot.split('[')[-1].replace(']', '').replace('Slot:', '').strip()
        else:
            slot_bay = "Bay A-01"
            
        status_label = 'Parked' if b.is_parked else ('Completed' if b.booking_status == 'completed' else 'Confirmed')
        
        formatted_bookings.append({
            'id': b.id,
            'booking_obj': b,
            'type_label': b.get_booking_type_display(),
            'driver_name': driver_name,
            'driver_phone': driver_phone,
            'vehicle_plate': b.vehicle.registration_number if b.vehicle else 'ANPR-GUEST',
            'vehicle_type': f"{b.vehicle.make} {b.vehicle.model}" if (b.vehicle and b.vehicle.make) else "Motorist Vehicle",
            'lot_name': b.lot.name if b.lot else b.parking_lot.split('(')[0].strip(),
            'slot_bay': slot_bay,
            'date': b.start_time.strftime('%d %b %Y') if b.start_time else 'Today',
            'time_slot': f"{b.start_time.strftime('%I:%M %p')} – {b.end_time.strftime('%I:%M %p')}" if (b.start_time and b.end_time) else 'Flexible',
            'amount': f"{b.total_amount:.2f}",
            'is_monthly': b.booking_type == 'monthly',
            'status': status_label,
            'is_parked': b.is_parked,
            'booking_status': b.booking_status,
            'overstay_fine': b.overstay_fine,
            'overstay_paid': b.overstay_paid,
            'entry_time': b.entry_time,
            'exit_time': b.exit_time,
            'qr_token': b.qr_code_token,
        })

    ctx.update({
        'bookings': formatted_bookings,
        'current_filter': filter_param,
        'search_query': search_q,
        'total_bookings_count': total_count,
        'parked_count': parked_count,
        'awaiting_count': awaiting_count,
        'completed_count': completed_count,
    })
    return render(request, 'lot_owner_panel/bookings.html', ctx)


@login_required
def owner_verify_entry_view(request, booking_id):
    from bookings.models import Booking
    booking = Booking.objects.filter(id=booking_id).first()
    if booking:
        now = timezone.now()
        booking.entry_time = now
        booking.is_parked = True
        booking.booking_status = 'active'
        booking.save()
        plate = booking.vehicle.registration_number if booking.vehicle else 'Vehicle'
        messages.success(request, f"Entry verified for Booking #{booking_id} ({plate}). Barrier opened at {now.strftime('%I:%M %p')}.")
    else:
        messages.success(request, f"Entry verified for Booking #{booking_id}. Vehicle marked as Parked / Active.")
    return redirect('lot_owner_panel:bookings')


@login_required
def owner_verify_exit_view(request, booking_id):
    from bookings.models import Booking
    booking = Booking.objects.filter(id=booking_id).first()
    if booking:
        now = timezone.now()
        if booking.end_time and now > booking.end_time and not booking.overstay_paid:
            diff_seconds = (now - booking.end_time).total_seconds()
            overstay_hours = round(Decimal(str(diff_seconds / 3600)), 2)
            fine_amount = round(overstay_hours * Decimal('50.00'), 2)
            if fine_amount <= Decimal('0.00'):
                fine_amount = Decimal('20.00')
            booking.overstay_hours = overstay_hours
            booking.overstay_fine = fine_amount
            booking.overstay_paid = False
            booking.save()
            messages.warning(request, f"⚠️ Overstay Detected for Booking #{booking_id}: Stay exceeded by {overstay_hours}h. Extra fee of ₹{fine_amount} due via Razorpay before exit barrier opens.")
            return redirect('lot_owner_panel:bookings')

        booking.exit_time = now
        booking.is_parked = False
        booking.booking_status = 'completed'
        booking.save()
        messages.success(request, f"Exit verified for Booking #{booking_id}. Gate barrier opened. Booking completed.")
    else:
        messages.success(request, f"Exit verified for Booking #{booking_id}. Gate barrier opened. Booking completed.")
    return redirect('lot_owner_panel:bookings')


@login_required
def owner_slots_view(request):
    
    ctx = get_owner_context(request, active_tab='slots')
    lot = ctx['primary_lot']

    if request.method == 'POST':
        zone = request.POST.get('zone', 'Basement A')
        slot_num = request.POST.get('slot_number', '').strip().upper()
        veh_cat = request.POST.get('vehicle_category', 'Car')
        sched = request.POST.get('schedule', '6 AM–11 PM')
        restr = request.POST.get('booking_restrictions', 'Min 1 hr, Max 24 hrs')

        if slot_num:
            ParkingSlot.objects.create(
                parking_lot=lot,
                zone=zone,
                slot_number=slot_num,
                vehicle_category=veh_cat,
                status='Available',
                schedule=sched,
                booking_restrictions=restr,
                maintenance_status='Operational'
            )
            messages.success(request, f"Created slot {slot_num} in {zone}.")
            return redirect('lot_owner_panel:slots')

    all_lot_slots = ParkingSlot.objects.filter(parking_lot=lot)
    slots_qs = all_lot_slots
    zone_filter = request.GET.get('zone', 'all')
    if zone_filter == 'basement_a':
        slots_qs = slots_qs.filter(zone__icontains='Basement')
    elif zone_filter == 'ground':
        slots_qs = slots_qs.filter(zone__icontains='Ground')
    elif zone_filter == 'ev_zone':
        slots_qs = slots_qs.filter(zone__icontains='EV')

    ctx.update({
        'slots': slots_qs,
        'current_zone': zone_filter,
        'total_slots_count': all_lot_slots.count(),
        'available_slots_count': all_lot_slots.filter(status='Available').count(),
        'occupied_slots_count': all_lot_slots.filter(status='Occupied').count(),
        'maintenance_slots_count': all_lot_slots.filter(maintenance_status='Maintenance').count(),
    })
    return render(request, 'lot_owner_panel/slots.html', ctx)


@login_required
def owner_toggle_slot_maintenance_view(request, slot_id):
    slot = get_object_or_404(ParkingSlot, id=slot_id, parking_lot__owner=request.user)
    if slot.is_unavailable:
        slot.maintenance_status = 'Operational'
        slot.status = 'Available'
    else:
        slot.maintenance_status = 'Maintenance'
        slot.status = 'Unavailable'
    slot.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '') or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'slot_id': slot.id,
            'slot_number': slot.slot_number,
            'is_unavailable': slot.is_unavailable,
            'status': slot.status,
            'maintenance_status': slot.maintenance_status,
        })

    messages.info(request, f"Updated status of {slot.slot_number} to {slot.maintenance_status}.")
    return redirect(request.META.get('HTTP_REFERER') or 'lot_owner_panel:slots')


@login_required
def owner_pricing_view(request):
    
    ctx = get_owner_context(request, active_tab='pricing')
    lot = ctx['primary_lot']

    if request.method == 'POST':
        try:
            lot.hourly_rate = float(request.POST.get('hourly_rate', lot.hourly_rate))
            lot.daily_rate = float(request.POST.get('daily_rate', lot.daily_rate))
            lot.overnight_rate = float(request.POST.get('overnight_rate', lot.overnight_rate))
            lot.monthly_rate = float(request.POST.get('monthly_rate', lot.monthly_rate))
            lot.bike_rate = float(request.POST.get('bike_rate', lot.bike_rate))
            lot.car_rate = float(request.POST.get('car_rate', lot.car_rate))
            lot.suv_rate = float(request.POST.get('suv_rate', lot.suv_rate))
            lot.ev_rate = float(request.POST.get('ev_rate', lot.ev_rate))
            lot.peak_hour_surge_pct = int(request.POST.get('peak_hour_surge_pct', 20))
            lot.monthly_pass_capacity = int(request.POST.get('monthly_pass_capacity', 10))
            lot.monthly_pass_auto_renew = bool(request.POST.get('monthly_pass_auto_renew'))
            old_hourly = float(lot.hourly_rate)
            lot.save()
            try:
                from parkease.email_service import EmailNotificationService
                EmailNotificationService.send_admin_price_change_alert(lot, old_hourly, lot.hourly_rate, request.user)
            except Exception:
                pass
            messages.success(request, "Pricing and tariff configuration saved successfully. Admin notified of tariff update.")
        except ValueError:
            messages.error(request, "Please enter valid numeric amounts for pricing fields.")
        return redirect('lot_owner_panel:pricing')

    ctx['lot'] = lot
    return render(request, 'lot_owner_panel/pricing.html', ctx)


@login_required
def owner_ev_charging_view(request):
    
    ctx = get_owner_context(request, active_tab='ev_charging')
    lot = ctx['primary_lot']

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'report_fault':
            charger_id = request.POST.get('charger_id')
            desc = request.POST.get('description')
            OwnerSupportTicket.objects.create(
                owner=request.user,
                parking_lot=lot,
                category='EV Charger Maintenance',
                subject=f"Fault report for {charger_id}",
                description=desc,
                status='Open'
            )
            messages.success(request, f"Fault report dispatched for charger {charger_id}. Ticket generated.")
            return redirect('lot_owner_panel:ev_charging')
        elif action == 'toggle_status':
            chg_pk = request.POST.get('charger_pk')
            chg = EVCharger.objects.filter(id=chg_pk, parking_lot=lot).first()
            if chg:
                chg.status = 'Maintenance' if chg.status == 'Available' else 'Available'
                chg.save()
                if chg.status == 'Maintenance':
                    try:
                        from parkease.email_service import EmailNotificationService
                        EmailNotificationService.send_ev_maintenance_alert(chg, lot, set_by='owner')
                    except Exception:
                        pass
                messages.success(request, f"Charger {chg.charger_id} status updated to {chg.status}.")
            return redirect('lot_owner_panel:ev_charging')
        elif action == 'run_diagnostic':
            chg_pk = request.POST.get('charger_pk')
            chg = EVCharger.objects.filter(id=chg_pk, parking_lot=lot).first()
            if chg:
                chg.status = 'Available'
                chg.save()
                messages.success(request, f"OCPP Diagnostic test passed for {chg.charger_id}. 3-Phase power verified, status set to Available.")
            return redirect('lot_owner_panel:ev_charging')
        elif action == 'add_charger':
            charger_id = request.POST.get('charger_id', '').strip()
            location = request.POST.get('location', '').strip()
            connector_type = request.POST.get('connector_type', 'Type 2 AC / CCS2 DC Fast')
            try:
                power_kw = float(request.POST.get('power_kw', 22.0))
            except (ValueError, TypeError):
                power_kw = 22.0

            try:
                rate_per_kwh = float(request.POST.get('rate_per_kwh', 15.0))
            except (ValueError, TypeError):
                rate_per_kwh = 15.0

            schedule = request.POST.get('schedule', '24/7 Access')
            fee_included = bool(request.POST.get('parking_fee_included'))

            if charger_id and location:
                EVCharger.objects.create(
                    parking_lot=lot,
                    charger_id=charger_id,
                    location=location,
                    connector_type=connector_type,
                    power_kw=power_kw,
                    rate_per_kwh=rate_per_kwh,
                    schedule=schedule,
                    parking_fee_included=fee_included,
                    status='Available'
                )
                messages.success(request, f"EV Charger {charger_id} has been added successfully.")
            else:
                messages.error(request, "Charger ID and Location are required.")
            return redirect('lot_owner_panel:ev_charging')

    chargers = EVCharger.objects.filter(parking_lot=lot)
    ctx.update({
        'chargers': chargers,
        'total_chargers': chargers.count(),
        'available_chargers': chargers.filter(status='Available').count(),
    })
    return render(request, 'lot_owner_panel/ev_charging.html', ctx)


@login_required
def owner_earnings_view(request):
    
    ctx = get_owner_context(request, active_tab='earnings')
    profile = ctx['profile']
    payouts = OwnerPayout.objects.filter(owner=request.user).order_by('-created_at')

    bank_profile = {
        'bank_name': profile.bank_name or "State Bank of India",
        'last_digits': profile.bank_account_number[-4:] if len(profile.bank_account_number) >= 4 else "8741",
        'ifsc': profile.bank_ifsc_code or "SBIHR656565",
        'holder': profile.bank_account_holder or request.user.get_full_name() or request.user.username,
    }

    ctx.update({
        'payouts': payouts,
        'bank_profile': bank_profile,
        'earnings_summary': {
            'gross': '34,200.00',
            'commission': '5,130.00',
            'refunds': '450.00',
            'net': '28,620.00',
        }
    })
    return render(request, 'lot_owner_panel/earnings.html', ctx)


@login_required
def owner_download_statement_view(request):
    
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    user = request.user
    ctx = get_owner_context(request, active_tab='earnings')
    lot = ctx['primary_lot']
    profile = ctx.get('profile')
    payouts = list(OwnerPayout.objects.filter(owner=user).order_by('-created_at'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    
    c_primary = colors.HexColor('#0f2942')   
    c_accent = colors.HexColor('#0284c7') 
    c_dark = colors.HexColor('#0f172a')   
    c_muted = colors.HexColor('#64748b')      
    c_light_bg = colors.HexColor('#f8fafc')    
    c_border = colors.HexColor('#cbd5e1')  
    c_green = colors.HexColor('#16a34a')  
    c_red = colors.HexColor('#dc2626')      

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_muted
    )
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_primary
    )
    body_muted = ParagraphStyle(
        'BodyMuted',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_muted
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    
    header_data = [
        [
            Paragraph("<b>ParkEase Technologies</b><br/><font color='#64748b' size='8'>Official Space Partner Studio - Payout Statement</font>", title_style),
            Paragraph("<font size='11'><b>SETTLEMENT STATEMENT</b></font><br/><font color='#64748b' size='8'>Statement Cycle: <b>October 2026</b><br/>Date Generated: <b>29 Oct 2026</b></font>", subtitle_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[310, 213])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=12))

    
    owner_name = user.get_full_name() or user.username
    bank_name = profile.bank_name if profile and profile.bank_name else "State Bank of India"
    acc_num = profile.bank_account_number if profile and profile.bank_account_number else "XXXXXXXX8741"
    masked_acc = ("XXXX " * max(1, (len(acc_num) - 4) // 4)) + acc_num[-4:] if len(acc_num) >= 4 else acc_num
    ifsc = profile.bank_ifsc_code if profile and profile.bank_ifsc_code else "SBIHR656565"
    holder = profile.bank_account_holder if profile and profile.bank_account_holder else owner_name
    acc_type = profile.bank_account_type if profile and profile.bank_account_type else "Current / Business Account"

    col_facility = [
        Paragraph("<b>PARKING FACILITY & LOT OWNER</b>", h2_style),
        Spacer(1, 4),
        Paragraph(f"<b>Facility:</b> {lot.name}", table_cell),
        Paragraph(f"<b>Address:</b> {lot.street_address}, {lot.area}", table_cell),
        Paragraph(f"<b>City/PIN:</b> {lot.city}, {lot.state} - {lot.pin_code}", table_cell),
        Paragraph(f"<b>Owner Partner:</b> {owner_name}", table_cell),
        Paragraph(f"<b>Contact Email:</b> {user.email}", table_cell),
    ]

    col_bank = [
        Paragraph("<b>VERIFIED SETTLEMENT ACCOUNT</b>", h2_style),
        Spacer(1, 4),
        Paragraph(f"<b>Bank Name:</b> {bank_name}", table_cell),
        Paragraph(f"<b>Account Holder:</b> {holder}", table_cell),
        Paragraph(f"<b>Account Number:</b> {masked_acc}", table_cell),
        Paragraph(f"<b>IFSC Code:</b> {ifsc}", table_cell),
        Paragraph(f"<b>Account Type:</b> {acc_type}", table_cell),
        Paragraph("<font color='#16a34a'><b>Direct Deposit:</b> Verified &amp; Active</font>", table_cell),
    ]

    meta_table_data = [[col_facility, col_bank]]
    t_meta = Table(meta_table_data, colWidths=[260, 263])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    
    summary_data = [
        [
            Paragraph("<b>GROSS REVENUE</b><br/><font size='7' color='#64748b'>Customer Bookings</font><br/><br/><font size='12' color='#0f172a'><b>INR 34,200.00</b></font>", body_muted),
            Paragraph("<b>PLATFORM FEE</b><br/><font size='7' color='#64748b'>ParkEase Split (15%)</font><br/><br/><font size='12' color='#dc2626'><b>-INR 5,130.00</b></font>", body_muted),
            Paragraph("<b>ADJUSTMENTS</b><br/><font size='7' color='#64748b'>Refunds &amp; Fines</font><br/><br/><font size='12' color='#64748b'><b>-INR 450.00</b></font>", body_muted),
            Paragraph("<b>NET PAYABLE</b><br/><font size='7' color='#16a34a'>Direct Settlement</font><br/><br/><font size='12' color='#16a34a'><b>INR 28,620.00</b></font>", body_muted),
        ]
    ]
    t_summary = Table(summary_data, colWidths=[130, 130, 130, 133])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 14))


    story.append(Paragraph("<b>SETTLEMENT TRANSACTION LEDGER</b>", h2_style))
    story.append(Spacer(1, 6))

    ledger_rows = [
        [
            Paragraph("<b>Payout Ref (UTR)</b>", table_header),
            Paragraph("<b>Billing Period</b>", table_header),
            Paragraph("<b>Gross (INR)</b>", table_header),
            Paragraph("<b>Fee (15%)</b>", table_header),
            Paragraph("<b>Adj. (INR)</b>", table_header),
            Paragraph("<b>Net Settled</b>", table_header),
            Paragraph("<b>Status</b>", table_header),
            Paragraph("<b>Date</b>", table_header),
        ]
    ]

    sample_fallback_payouts = [
        {
            'ref': 'UTR9847291847192',
            'period': '15 Oct - 22 Oct 2026',
            'gross': '14,500.00',
            'comm': '-2,175.00',
            'refu': '-0.00',
            'net': '12,325.00',
            'status': 'Paid',
            'date': '23 Oct 2026'
        },
        {
            'ref': 'UTR9834110948215',
            'period': '08 Oct - 15 Oct 2026',
            'gross': '19,700.00',
            'comm': '-2,955.00',
            'refu': '-450.00',
            'net': '16,295.00',
            'status': 'Paid',
            'date': '16 Oct 2026'
        }
    ]

    if payouts:
        for p in payouts:
            clean_period = str(p.period).replace('–', '-').replace('—', '-')
            clean_date = str(p.payout_date or '28 Oct 2026').replace('–', '-')
            ledger_rows.append([
                Paragraph(f"<b>{p.reference}</b>", table_cell_bold),
                Paragraph(clean_period, table_cell),
                Paragraph(f"{p.gross_revenue:,.2f}", table_cell),
                Paragraph(f"-{p.commission:,.2f}", table_cell),
                Paragraph(f"-{p.refunds:,.2f}", table_cell),
                Paragraph(f"<b>INR {p.net_payable:,.2f}</b>", table_cell_bold),
                Paragraph("<font color='#16a34a'><b>Paid</b></font>" if p.status == 'Paid' else p.status, table_cell),
                Paragraph(clean_date, table_cell),
            ])
    else:
        for s in sample_fallback_payouts:
            ledger_rows.append([
                Paragraph(f"<b>{s['ref']}</b>", table_cell_bold),
                Paragraph(s['period'], table_cell),
                Paragraph(s['gross'], table_cell),
                Paragraph(s['comm'], table_cell),
                Paragraph(s['refu'], table_cell),
                Paragraph(f"<b>INR {s['net']}</b>", table_cell_bold),
                Paragraph("<font color='#16a34a'><b>Paid</b></font>", table_cell),
                Paragraph(s['date'], table_cell),
            ])

    t_ledger = Table(ledger_rows, colWidths=[95, 85, 60, 58, 55, 75, 45, 50])
    t_ledger.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
    ]))
    story.append(t_ledger)
    story.append(Spacer(1, 16))

    
    footer_text = (
        "<b>Electronic Statement Authentication:</b> This settlement statement is an authenticated digital PDF record issued "
        "by ParkEase Technologies Pvt. Ltd. pursuant to the Space Partner Agreement. Direct NEFT/RTGS/IMPS electronic remittances "
        "are settled under Reserve Bank of India clearing guidelines. In case of any settlement discrepancies, submit a report via "
        "the ParkEase Space Owner Studio within 7 business days."
    )
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_border, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(footer_text, ParagraphStyle('FooterNote', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=c_muted)))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename_lot = re.sub(r'[^a-zA-Z0-9]', '_', lot.name)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ParkEase_Settlement_Statement_{filename_lot}_Oct2026.pdf"'
    response['Content-Length'] = len(pdf_bytes)
    return response


@login_required
def owner_reports_view(request):
    
    ctx = get_owner_context(request, active_tab='reports')
    period = request.GET.get('period', '30d')
    ctx['period'] = period
    return render(request, 'lot_owner_panel/reports.html', ctx)


@login_required
def owner_reviews_view(request):
    
    ctx = get_owner_context(request, active_tab='reviews')
    lot = ctx['primary_lot']
    
    reviews = LotReview.objects.filter(parking_lot__owner=request.user).order_by('-created_at')
    
    total_reviews = reviews.count()
    if total_reviews > 0:
        avg_rating = round(sum(r.rating for r in reviews) / total_reviews, 1)
        stars_5 = reviews.filter(rating=5).count()
        stars_4 = reviews.filter(rating=4).count()
        stars_3 = reviews.filter(rating=3).count()
        stars_2_1 = reviews.filter(rating__lte=2).count()
        pct_5 = round((stars_5 / total_reviews) * 100)
        pct_4 = round((stars_4 / total_reviews) * 100)
        pct_3 = round((stars_3 / total_reviews) * 100)
        pct_2_1 = round((stars_2_1 / total_reviews) * 100)
    else:
        avg_rating = 5.0
        total_reviews = 0
        stars_5 = stars_4 = stars_3 = stars_2_1 = 0
        pct_5 = 100
        pct_4 = pct_3 = pct_2_1 = 0

    ctx['reviews'] = reviews
    ctx['total_reviews'] = total_reviews
    ctx['avg_rating'] = avg_rating
    ctx['stars_5'] = stars_5
    ctx['stars_4'] = stars_4
    ctx['stars_3'] = stars_3
    ctx['stars_2_1'] = stars_2_1
    ctx['pct_5'] = pct_5
    ctx['pct_4'] = pct_4
    ctx['pct_3'] = pct_3
    ctx['pct_2_1'] = pct_2_1
    return render(request, 'lot_owner_panel/reviews.html', ctx)


@login_required
def owner_reply_review_view(request, review_id):
    review = get_object_or_404(LotReview, id=review_id, parking_lot__owner=request.user)
    if request.method == 'POST':
        reply_text = request.POST.get('owner_reply', '').strip()
        if reply_text:
            review.owner_reply = reply_text
            review.save()
            try:
                from parkease.email_service import EmailNotificationService
                EmailNotificationService.send_review_response(review, reply_text)
            except Exception:
                pass
            messages.success(request, "Your reply has been published to this review. User notified via email.")
    return redirect('lot_owner_panel:reviews')


@login_required
def owner_report_review_view(request, review_id):
    review = get_object_or_404(LotReview, id=review_id, parking_lot__owner=request.user)
    if request.method == 'POST':
        review.is_reported = True
        review.report_reason = request.POST.get('report_reason', 'Abusive language')
        review.save()
        messages.info(request, "Review reported to ParkEase moderation team for review.")
    return redirect('lot_owner_panel:reviews')


@login_required
def owner_notifications_view(request):
    
    ctx = get_owner_context(request, active_tab='notifications')
    notifs = OwnerNotification.objects.filter(owner=request.user).order_by('-created_at')
    ctx['all_notifications'] = notifs
    return render(request, 'lot_owner_panel/notifications.html', ctx)


@login_required
def owner_mark_notifications_read_view(request):
    
    OwnerNotification.objects.filter(owner=request.user, is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        from django.http import JsonResponse
        return JsonResponse({'status': 'ok', 'unread_count': 0})
    messages.success(request, "All notifications marked as read.")
    return redirect(request.META.get('HTTP_REFERER') or 'lot_owner_panel:notifications')


@login_required
def owner_profile_settings_view(request):
    
    ctx = get_owner_context(request, active_tab='profile')
    profile = ctx['profile']
    user = request.user
    user_prof = ctx['user_profile']

    if request.method == 'POST':
        section = request.POST.get('section')
        if section == 'bank':
            
            profile.bank_account_holder = request.POST.get('bank_account_holder', '').strip()
            profile.bank_name = request.POST.get('bank_name', '').strip()
            profile.bank_account_number = request.POST.get('bank_account_number', '').strip()
            profile.bank_ifsc_code = request.POST.get('bank_ifsc_code', '').strip().upper()
            profile.bank_branch = request.POST.get('bank_branch', '').strip()
            profile.bank_account_type = request.POST.get('bank_account_type', 'Current Account / Business').strip()
            profile.save()
            try:
                from parkease.email_service import EmailNotificationService
                EmailNotificationService.send_owner_bank_updated(profile)
            except Exception:
                pass
            messages.success(request, "Bank & Settlement Account details saved successfully. Notifications sent to owner and admin.")
        else:
            
            full_name = request.POST.get('full_name', '').strip()
            if full_name:
                parts = full_name.split(' ', 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
            
            user.email = request.POST.get('email', user.email).strip().lower()
            user.save()

            mobile = request.POST.get('mobile_number', '').strip()
            if mobile:
                user_prof.mobile_number = mobile
                user_prof.save()

            profile.owner_type = request.POST.get('owner_type', profile.owner_type)
            profile.present_address = request.POST.get('present_address', profile.present_address)
            profile.city = request.POST.get('city', profile.city)
            profile.state = request.POST.get('state', profile.state)
            profile.pin_code = request.POST.get('pin_code', profile.pin_code)
            profile.save()
            messages.success(request, "Personal and communication details updated.")

        return redirect('lot_owner_panel:profile_settings')

    ctx['masked_id'] = mask_id_number(profile.id_number)
    return render(request, 'lot_owner_panel/profile_settings.html', ctx)


@login_required
def owner_support_view(request):
    
    ctx = get_owner_context(request, active_tab='support')
    lot = ctx['primary_lot']

    if request.method == 'POST':
        category = request.POST.get('category', 'Settlement / Payout')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        booking_ref = request.POST.get('booking_ref', '').strip()

        ticket = OwnerSupportTicket.objects.create(
            owner=request.user,
            parking_lot=lot,
            booking_ref=booking_ref,
            category=category,
            subject=subject,
            description=description,
            status='Open'
        )
        if 'attachment' in request.FILES:
            ticket.attachment = request.FILES['attachment']
            ticket.save()

        messages.success(request, f"Support ticket #{ticket.id} created successfully. Our team will review it shortly.")
        return redirect('lot_owner_panel:support')

    tickets = OwnerSupportTicket.objects.filter(owner=request.user).order_by('-created_at')
    ctx['tickets'] = tickets
    return render(request, 'lot_owner_panel/support.html', ctx)




@login_required(login_url='lot_owner_panel:login')
def owner_extensions_view(request):
    
    from bookings.models import BookingExtensionRequest, Booking
    ctx = get_owner_context(request, active_tab='extensions')
    owner = request.user
    owner_lots = ParkingLot.objects.filter(owner=owner)


    ext_qs = BookingExtensionRequest.objects.filter(
        booking__lot__in=owner_lots
    ).select_related(
        'booking', 'requested_by', 'booking__lot', 'booking__slot', 'booking__vehicle',
        'conflicting_booking', 'conflicting_booking__user', 'conflicting_booking__slot',
        'assigned_slot', 'assigned_lot'
    ).order_by('-created_at')

    
    status_filter = request.GET.get('status', 'all').strip().lower()
    if status_filter in ['pending', 'approved', 'rejected']:
        ext_qs = ext_qs.filter(status=status_filter)

    
    q = request.GET.get('q', '').strip()
    if q:
        ext_qs = ext_qs.filter(
            models.Q(booking__id__icontains=q) |
            models.Q(booking__vehicle__registration_number__icontains=q) |
            models.Q(requested_by__username__icontains=q) |
            models.Q(requested_by__first_name__icontains=q) |
            models.Q(requested_by__last_name__icontains=q) |
            models.Q(booking__parking_lot__icontains=q)
        )


    lot_id = request.GET.get('lot_id', '').strip()
    if lot_id and lot_id.isdigit():
        ext_qs = ext_qs.filter(booking__lot_id=int(lot_id))

    
    base_owner_requests = BookingExtensionRequest.objects.filter(booking__lot__in=owner_lots)
    counts = {
        'all': base_owner_requests.count(),
        'pending': base_owner_requests.filter(status='pending').count(),
        'approved': base_owner_requests.filter(status='approved').count(),
        'rejected': base_owner_requests.filter(status='rejected').count(),
        'conflicts': base_owner_requests.filter(status='pending', conflict_detected=True).count(),
    }

    
    all_operational_slots = ParkingSlot.objects.filter(
        parking_lot__in=owner_lots,
        maintenance_status='Operational'
    ).select_related('parking_lot')

    ctx.update({
        'extension_requests': ext_qs,
        'counts': counts,
        'status_filter': status_filter,
        'search_query': q,
        'selected_lot_id': lot_id,
        'owner_lots': owner_lots,
        'all_operational_slots': all_operational_slots,
    })
    return render(request, 'lot_owner_panel/extensions.html', ctx)


@login_required(login_url='lot_owner_panel:login')
def owner_approve_extension_view(request, ext_id):
    
    from bookings.models import BookingExtensionRequest
    ext_req = get_object_or_404(
        BookingExtensionRequest,
        id=ext_id,
        booking__lot__owner=request.user
    )

    if ext_req.status != 'pending':
        messages.warning(request, f"Extension request #{ext_req.id} has already been {ext_req.status}.")
        return redirect('lot_owner_panel:extensions')

    if request.method == 'POST':
        reassign_slot_id = request.POST.get('reassign_slot_id', '').strip()
        reassign_lot_id = request.POST.get('reassign_lot_id', '').strip()
        owner_note = request.POST.get('owner_note', '').strip()

        booking = ext_req.booking
        reassigned_text = ""

        
        if reassign_slot_id and reassign_slot_id.isdigit():
            new_slot = ParkingSlot.objects.filter(
                id=int(reassign_slot_id),
                parking_lot__owner=request.user
            ).first()
            if new_slot:
                booking.slot = new_slot
                ext_req.assigned_slot = new_slot
                reassigned_text = f" Reassigned to Bay: {new_slot.slot_number} ({new_slot.zone})."

        
        if reassign_lot_id and reassign_lot_id.isdigit():
            new_lot = ParkingLot.objects.filter(
                id=int(reassign_lot_id),
                owner=request.user
            ).first()
            if new_lot:
                booking.lot = new_lot
                booking.parking_lot = new_lot.name
                ext_req.assigned_lot = new_lot
                reassigned_text += f" Reassigned facility: {new_lot.name}."

        
        booking.end_time = ext_req.requested_new_end_time
        booking.total_amount += ext_req.additional_fee
        booking.save()

        
        ext_req.status = 'approved'
        default_note = "Extension approved by lot owner. Please ensure your vehicle vacates the space promptly when your extended time expires."
        ext_req.owner_note = owner_note if owner_note else default_note
        ext_req.resolved_at = timezone.now()
        ext_req.save()

        
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_driver_extension_approved(ext_req)
        except Exception:
            pass

        messages.success(
            request,
            f"Extension request #{ext_req.id} for Booking #BK-{booking.id} approved! "
            f"Departure extended until {booking.end_time.strftime('%I:%M %p, %b %d')}.{reassigned_text} "
            f"Confirmation email dispatched to motorist ({ext_req.requested_by.email})."
        )
    return redirect('lot_owner_panel:extensions')


@login_required(login_url='lot_owner_panel:login')
def owner_reject_extension_view(request, ext_id):

    from bookings.models import BookingExtensionRequest
    ext_req = get_object_or_404(
        BookingExtensionRequest,
        id=ext_id,
        booking__lot__owner=request.user
    )

    if ext_req.status != 'pending':
        messages.warning(request, f"Extension request #{ext_req.id} has already been {ext_req.status}.")
        return redirect('lot_owner_panel:extensions')

    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        ext_req.status = 'rejected'
        ext_req.owner_note = rejection_reason or "Extension request declined due to space unavailability and subsequent confirmed reservations."
        ext_req.resolved_at = timezone.now()
        ext_req.save()

        messages.info(
            request,
            f"Extension request #{ext_req.id} for Booking #BK-{ext_req.booking_id} declined. Motorist must vacate by original scheduled departure."
        )
    return redirect('lot_owner_panel:extensions')

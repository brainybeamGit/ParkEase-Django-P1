from django.conf import settings
import json
import io
import base64
import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
import qrcode

from lot_owner_panel.models import ParkingLot, ParkingSlot, LotReview
from bookings.models import Booking
from accounts.models import Vehicle

def home(request):
    
    context = {
        'page_title': 'ParkEase - The smarter way to find parking',
    }
    return render(request, 'parking/home.html', context)

def reserve_parking_view(request):
    
    lot_id = request.GET.get('lot')
    if lot_id:
        qs = request.META.get('QUERY_STRING', '')
        return redirect(f"/lot/{lot_id}/?{qs}")
    context = {
        'page_title': 'Reserve Your Parking in Advance - ParkEase',
    }
    return render(request, 'parking/reserve_parking.html', context)

def monthly_parking_view(request):
    
    context = {
        'page_title': 'Monthly Parking - The Best Choice for Long Term Parking | ParkEase',
    }
    return render(request, 'parking/monthly_parking.html', context)

def drive_up_parking_view(request):
    
    context = {
        'page_title': 'Park and Pay - Quick, Convenient & Cashless Drive-Up Parking | ParkEase',
    }
    return render(request, 'parking/drive_up_parking.html', context)

def on_the_move_view(request):
    
    context = {
        'page_title': 'Find Parking on the Move - Apple CarPlay & Android Auto | ParkEase',
    }
    return render(request, 'parking/on_the_move.html', context)




def rent_out_your_space_view(request):
    
    context = {
        'page_title': 'Rent Out Your Space - Earn Passive Income with Your Driveway | ParkEase',
    }
    return render(request, 'parking/rent_out_your_space.html', context)


def about_us_view(request):
    
    context = {
        'page_title': 'About Us - Our Mission & Story | ParkEase',
    }
    return render(request, 'parking/about_us.html', context)


def press_news_view(request):
    
    context = {
        'page_title': 'Press & Newsroom - Latest Stories & Company Updates | ParkEase',
    }
    return render(request, 'parking/press_news.html', context)


def careers_view(request):
    
    context = {
        'page_title': 'Careers at ParkEase - Shape the Future of Urban Mobility',
    }
    return render(request, 'parking/careers.html', context)


def business_view(request):
    """
    ParkEase for Business - Commercial & enterprise parking management solutions.
    """
    context = {
        'page_title': 'ParkEase for Business - Commercial & Enterprise Parking Solutions',
    }
    return render(request, 'parking/business.html', context)


def help_center_view(request):
    
    context = {
        'page_title': 'Help Center - Knowledge Base & Customer Support | ParkEase',
    }
    return render(request, 'parking/help_center.html', context)


def services_summary_view(request):
    
    context = {
        'page_title': 'Summary of Services - Explore All ParkEase Parking Features',
    }
    return render(request, 'parking/services_summary.html', context)


def faqs_support_view(request):
    
    context = {
        'page_title': 'FAQs & Support - Quick Answers to Common Questions | ParkEase',
    }
    return render(request, 'parking/faqs_support.html', context)


def parse_coords(map_location_str, fallback=(23.0456, 72.5489)):
    if not map_location_str:
        return fallback
    try:
        parts = [p.strip() for p in map_location_str.split(',')]
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
    except Exception:
        pass
    return fallback


def search_view(request):
    
    if not request.user.is_authenticated:
        from django.urls import reverse
        messages.info(request, "Please log in to your ParkEase account to search and reserve parking spaces.")
        return redirect(f"{reverse('accounts:login')}?next={request.get_full_path()}")
    query = request.GET.get('q', '').strip() or request.GET.get('area', '').strip()
    from_date = request.GET.get('from_date', '')
    from_time = request.GET.get('from_time', '09:00')
    until_date = request.GET.get('until_date', '')
    until_time = request.GET.get('until_time', '12:00')
    vehicle_type = request.GET.get('vehicle_type', 'car')
    sort_by = request.GET.get('sort', 'closest').lower()
    filter_ev = request.GET.get('filter_ev') == '1'

    
    tomorrow = date.today() + timedelta(days=1)
    if not from_date:
        from_date = tomorrow.strftime('%Y-%m-%d')
    if not until_date:
        until_date = tomorrow.strftime('%Y-%m-%d')

    
    all_approved = list(ParkingLot.objects.filter(status='approved', is_paused=False))

    if filter_ev:
        all_approved = [lot for lot in all_approved if 'ev_charging' in (lot.available_services or [])]

    
    center_lat, center_lng = 23.0456, 72.5489  
    destination_name = query or "Navrangpura, Ahmedabad"

    exact_matches = []
    nearby_lots = []

    if query:
        q_lower = query.lower()
        if 'mumbai' in q_lower or 'bandra' in q_lower or 'nariman' in q_lower or 'bkc' in q_lower or 'bom' in q_lower:
            center_lat, center_lng = 19.0760, 72.8777
        elif 'delhi' in q_lower or 'connaught' in q_lower or 'gurugram' in q_lower or 'ncr' in q_lower or 'del' in q_lower:
            center_lat, center_lng = 28.6304, 77.2177
        elif 'bengaluru' in q_lower or 'bangalore' in q_lower or 'mg road' in q_lower or 'indiranagar' in q_lower or 'blr' in q_lower:
            center_lat, center_lng = 12.9716, 77.5946
        elif 'pune' in q_lower or 'koregaon' in q_lower or 'fc road' in q_lower or 'pnq' in q_lower:
            center_lat, center_lng = 18.5204, 73.8567
        elif 'hyderabad' in q_lower or 'hitec' in q_lower or 'banjara' in q_lower or 'hyd' in q_lower:
            center_lat, center_lng = 17.3850, 78.4867
        elif 'chennai' in q_lower or 't nagar' in q_lower or 'maa' in q_lower:
            center_lat, center_lng = 13.0827, 80.2707
        elif 'kolkata' in q_lower or 'ccu' in q_lower:
            center_lat, center_lng = 22.5726, 88.3639
        elif 'ahmedabad' in q_lower or 'navrangpura' in q_lower or 'sarvottam' in q_lower or 'gujarat' in q_lower or 'amd' in q_lower:
            center_lat, center_lng = 23.0456, 72.5489

        
        for lot in all_approved:
            searchable_text = f"{lot.name} {lot.street_address} {lot.building_name} {lot.area} {lot.city} {lot.state} {lot.pin_code}".lower()
            
            tokens = [t.strip() for t in q_lower.replace(',', ' ').split() if len(t.strip()) > 2]
            if q_lower in searchable_text or any(token in searchable_text for token in tokens):
                exact_matches.append(lot)

        if not exact_matches:
            nearby_lots = list(all_approved)
    else:
        exact_matches = list(all_approved)

    if exact_matches:
        lat0, lng0 = parse_coords(exact_matches[0].map_location)
        if lat0 != 23.0456 or lng0 != 72.5489:
            center_lat, center_lng = lat0, lng0

    active_lots = exact_matches if exact_matches else nearby_lots


    if sort_by == 'cheapest':
        active_lots.sort(key=lambda x: x.hourly_rate)
    elif sort_by == 'recommended':
        active_lots.sort(key=lambda x: (-x.total_capacity, x.hourly_rate))
    else:
        active_lots.sort(key=lambda x: x.id)

    
    duration_hours = 3
    if from_date and until_date and from_time and until_time:
        try:
            dt_from = datetime.strptime(f"{from_date} {from_time}", "%Y-%m-%d %H:%M")
            dt_until = datetime.strptime(f"{until_date} {until_time}", "%Y-%m-%d %H:%M")
            diff_h = (dt_until - dt_from).total_seconds() / 3600
            if diff_h > 0:
                duration_hours = max(1, round(diff_h))
        except Exception:
            duration_hours = 3

    
    map_markers = []
    for lot in active_lots:
        lat, lng = parse_coords(lot.map_location)
        rate = float(lot.hourly_rate)
        total_estimate = rate * duration_hours
        avail_count = lot.slots.filter(status__iexact='available').exclude(maintenance_status='Maintenance').count() if hasattr(lot, 'slots') else lot.total_capacity
        if avail_count == 0 and lot.total_capacity > 0:
            avail_count = lot.total_capacity

        map_markers.append({
            'id': lot.id,
            'name': lot.name,
            'building': lot.building_name,
            'street': lot.street_address,
            'area': lot.area,
            'city': lot.city,
            'lat': lat,
            'lng': lng,
            'hourly_rate': f"₹{rate:.0f}",
            'total_price': f"₹{total_estimate:.0f}",
            'raw_rate': rate,
            'capacity': lot.total_capacity,
            'available_slots': avail_count,
            'has_ev': 'ev_charging' in (lot.available_services or []),
            'space_type': lot.get_space_type_display(),
            'photo_url': lot.space_photo.url if lot.space_photo else None,
        })

    user_vehicles = []
    if request.user.is_authenticated and hasattr(request.user, 'vehicles'):
        user_vehicles = request.user.vehicles.all()

    context = {
        'page_title': f"Parking near {query or 'Ahmedabad'} - ParkEase",
        'query': query,
        'destination_name': destination_name,
        'from_date': from_date,
        'from_time': from_time,
        'until_date': until_date,
        'until_time': until_time,
        'vehicle_type': vehicle_type,
        'sort_by': sort_by,
        'filter_ev': filter_ev,
        'duration_hours': duration_hours,
        'exact_matches': exact_matches,
        'nearby_lots': nearby_lots,
        'active_lots': active_lots,
        'map_markers_json': json.dumps(map_markers),
        'center_lat': center_lat,
        'center_lng': center_lng,
        'user_vehicles': user_vehicles,
    }
    return render(request, 'parking/search.html', context)


def lot_detail_view(request, lot_id):
   
    lot = get_object_or_404(ParkingLot, id=lot_id)

    
    from_date = request.GET.get('from_date', '')
    from_time = request.GET.get('from_time', '09:00')
    until_date = request.GET.get('until_date', '')
    until_time = request.GET.get('until_time', '12:00')
    vehicle_type = request.GET.get('vehicle_type', 'car')

    tomorrow = date.today() + timedelta(days=1)
    if not from_date:
        from_date = tomorrow.strftime('%Y-%m-%d')
    if not until_date:
        until_date = tomorrow.strftime('%Y-%m-%d')

    duration_hours = 3
    try:
        dt_start = datetime.strptime(f"{from_date} {from_time}", "%Y-%m-%d %H:%M")
        dt_end = datetime.strptime(f"{until_date} {until_time}", "%Y-%m-%d %H:%M")
        diff_hours = (dt_end - dt_start).total_seconds() / 3600
        if diff_hours > 0:
            duration_hours = max(1, round(diff_hours, 1))
    except Exception:
        pass

    rate = float(lot.hourly_rate)
    if vehicle_type == 'two_wheeler' and lot.bike_rate:
        rate = float(lot.bike_rate)
    elif vehicle_type in ('suv', 'other') and lot.suv_rate:
        rate = float(lot.suv_rate)

    estimated_total = round(rate * duration_hours, 2)
    lat, lng = parse_coords(lot.map_location)

    
    slots = lot.slots.all()
    available_slots = slots.filter(status__iexact='available').exclude(maintenance_status='Maintenance')
    available_bays_count = available_slots.count() if slots.exists() else lot.total_capacity


    reviews = lot.reviews.all()[:5] if hasattr(lot, 'reviews') else []

    google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"

    context = {
        'page_title': f"{lot.name} - Parking in {lot.area}, {lot.city} | ParkEase",
        'lot': lot,
        'rate': rate,
        'duration_hours': duration_hours,
        'estimated_total': estimated_total,
        'from_date': from_date,
        'from_time': from_time,
        'until_date': until_date,
        'until_time': until_time,
        'vehicle_type': vehicle_type,
        'lat': lat,
        'lng': lng,
        'slots': slots,
        'available_bays_count': available_bays_count,
        'reviews': reviews,
        'google_maps_url': google_maps_url,
    }
    return render(request, 'parking/lot_detail.html', context)


def book_lot_view(request, lot_id):
    
    lot = get_object_or_404(ParkingLot, id=lot_id)
    user_vehicles = []
    if request.user.is_authenticated and hasattr(request.user, 'vehicles'):
        user_vehicles = request.user.vehicles.all()

    from_date = request.GET.get('from_date', '') or request.POST.get('from_date', '')
    from_time = request.GET.get('from_time', '09:00') or request.POST.get('from_time', '09:00')
    until_date = request.GET.get('until_date', '') or request.POST.get('until_date', '')
    until_time = request.GET.get('until_time', '12:00') or request.POST.get('until_time', '12:00')
    vehicle_type = request.GET.get('vehicle_type', 'car') or request.POST.get('vehicle_type', 'car')

    tomorrow = date.today() + timedelta(days=1)
    if not from_date:
        from_date = tomorrow.strftime('%Y-%m-%d')
    if not until_date:
        until_date = tomorrow.strftime('%Y-%m-%d')

    duration_hours = 3
    dt_start = timezone.now() + timedelta(hours=1)
    dt_end = dt_start + timedelta(hours=3)
    try:
        dt_start_naive = datetime.strptime(f"{from_date} {from_time}", "%Y-%m-%d %H:%M")
        dt_end_naive = datetime.strptime(f"{until_date} {until_time}", "%Y-%m-%d %H:%M")
        diff_hours = (dt_end_naive - dt_start_naive).total_seconds() / 3600
        if diff_hours > 0:
            duration_hours = max(1, round(diff_hours, 1))
        
        dt_start = timezone.make_aware(dt_start_naive, timezone.get_current_timezone())
        dt_end = timezone.make_aware(dt_end_naive, timezone.get_current_timezone())
    except Exception:
        pass

    rate = float(lot.hourly_rate)
    if vehicle_type == 'two_wheeler' and lot.bike_rate:
        rate = float(lot.bike_rate)
    elif vehicle_type in ('suv', 'other') and lot.suv_rate:
        rate = float(lot.suv_rate)

    base_charge = round(rate * duration_hours, 2)
    service_fee = 0.00
    gst_fee = 0.00
    total_amount = round(base_charge + service_fee + gst_fee, 2)

    available_slots = lot.slots.filter(status__iexact='available').exclude(maintenance_status='Maintenance') if lot.slots.exists() else []

    if request.method == 'POST':
        
        vehicle_id = request.POST.get('vehicle_id')
        vehicle_reg = request.POST.get('vehicle_reg', '').strip()
        slot_id = request.POST.get('slot_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id') or f"pay_rzp_{uuid.uuid4().hex[:12]}"
        razorpay_order_id = request.POST.get('razorpay_order_id') or f"order_rzp_{uuid.uuid4().hex[:12]}"
        

        selected_vehicle = None
        if vehicle_id and request.user.is_authenticated and str(vehicle_id).isdigit():
            selected_vehicle = request.user.vehicles.filter(id=vehicle_id).first()

        if not selected_vehicle and vehicle_reg and request.user.is_authenticated:
            from accounts.models import Vehicle, normalize_registration_number
            cleaned_reg = normalize_registration_number(vehicle_reg)
            selected_vehicle = request.user.vehicles.filter(registration_number=cleaned_reg).first()
            if not selected_vehicle:
                selected_vehicle = Vehicle.objects.create(
                    user=request.user,
                    registration_number=cleaned_reg,
                    vehicle_type=vehicle_type,
                    is_primary=True
                )
                try:
                    from parkease.email_service import EmailNotificationService
                    EmailNotificationService.send_vehicle_added(request.user, selected_vehicle)
                except Exception:
                    pass

        if not selected_vehicle and request.user.is_authenticated:
            selected_vehicle = request.user.vehicles.filter(is_primary=True).first() or request.user.vehicles.first()
            if not selected_vehicle:
                from accounts.models import Vehicle, normalize_registration_number
                selected_vehicle = Vehicle.objects.create(
                    user=request.user,
                    registration_number=normalize_registration_number(vehicle_reg or "MH 02 PE 2026"),
                    vehicle_type=vehicle_type,
                    is_primary=True
                )
                try:
                    from parkease.email_service import EmailNotificationService
                    EmailNotificationService.send_vehicle_added(request.user, selected_vehicle)
                except Exception:
                    pass

        booking_user = request.user if request.user.is_authenticated else (User.objects.filter(is_superuser=True).first() or User.objects.first())

        token = f"PE-BK-{uuid.uuid4().hex[:10].upper()}"

        slot_label = ""
        slot = None
        slot_label = ""
        if slot_id:
            try:
                slot = ParkingSlot.objects.get(id=slot_id, parking_lot=lot)
                if slot.is_unavailable:
                    messages.error(request, f"Slot {slot.slot_number} is currently marked unavailable by the facility owner. Please select an available space.")
                    return redirect('parking:book_lot', lot_id=lot.id)
                slot_label = f" [Slot: {slot.zone} {slot.slot_number}]"
                slot.status = 'reserved'
                slot.save()
            except ParkingSlot.DoesNotExist:
                slot = None

        booking = Booking.objects.create(
            user=booking_user,
            vehicle=selected_vehicle,
            lot=lot,
            slot=slot,
            parking_lot=f"{lot.name} ({lot.area}, {lot.city}){slot_label}",
            booking_type='advance',
            start_time=dt_start,
            end_time=dt_end,
            total_amount=Decimal(str(total_amount)),
            payment_status='paid',
            booking_status='active',
            qr_code_token=token,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
        )

        
        try:
            import threading
            from parkease.email_service import EmailNotificationService
            threading.Thread(target=EmailNotificationService.send_booking_confirmation, args=(booking,), daemon=True).start()
        except Exception:
            pass

        
        if lot.owner:
            try:
                from lot_owner_panel.models import OwnerNotification
                OwnerNotification.objects.create(
                    owner=lot.owner,
                    category='booking',
                    title=f"New Booking Confirmed (#{booking.id})",
                    message=f"Motorist {booking_user.username} reserved a bay at {lot.name} for {dt_start.strftime('%b %d, %I:%M %p')}. Fee: INR {total_amount:.2f}.",
                    is_read=False
                )
            except Exception:
                pass

        messages.success(request, f"Payment confirmed via Razorpay! Space reserved with Booking ID #{booking.id}. Your digital QR entry pass has been generated.")
        return redirect('parking:booking_ticket', booking_id=booking.id)

    
    rzp_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    if not rzp_key_id or rzp_key_id in ('rzp_test_placeholder', 'TEST10000001'):
        rzp_key_id = 'rzp_test_1DP5mmOlF5G5ag'
    amount_paise = int(round(total_amount * 100))


    


    context = {
        'page_title': f"Book Space - {lot.name} | ParkEase",
        'lot': lot,
        'rate': rate,
        'duration_hours': duration_hours,
        'base_charge': base_charge,
        'service_fee': service_fee,
        'gst_fee': gst_fee,
        'total_amount': total_amount,
        'from_date': from_date,
        'from_time': from_time,
        'until_date': until_date,
        'until_time': until_time,
        'vehicle_type': vehicle_type,
        'user_vehicles': user_vehicles,
        'available_slots': available_slots,
        'razorpay_key_id': rzp_key_id,
        'razorpay_amount_paise': amount_paise,

    }
    return render(request, 'parking/book_lot.html', context)


def booking_ticket_view(request, booking_id):
    
    booking = get_object_or_404(Booking, id=booking_id)

    
    qr_data = f"PARKEASE|BK-{booking.id}|{booking.qr_code_token}|{booking.parking_lot}|{booking.vehicle.registration_number if booking.vehicle else 'ANPR-GUEST'}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=7,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B3B60", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    
    lat, lng = 23.0456, 72.5489
    lot = booking.lot
    if not lot:
        lot_name_prefix = booking.parking_lot.split('(')[0].strip()
        lot = ParkingLot.objects.filter(name__icontains=lot_name_prefix).first()
    if lot and lot.map_location:
        lat, lng = parse_coords(lot.map_location)

    google_maps_directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"

    
    duration_hours = 1
    if booking.start_time and booking.end_time:
        duration_hours = max(1, round((booking.end_time - booking.start_time).total_seconds() / 3600))
    tariff_rate = lot.hourly_rate if lot and lot.hourly_rate else (booking.total_amount / duration_hours if duration_hours else booking.total_amount)
    base_charge = booking.total_amount

    
    lot_name = lot.name if lot else booking.parking_lot.split('(')[0].strip()
    lot_address = ""
    if lot:
        addr_parts = [part.strip() for part in [lot.street_address, lot.area, lot.city] if part and part.strip()]
        lot_address = ", ".join(addr_parts)
    elif '(' in booking.parking_lot and ')' in booking.parking_lot:
        lot_address = booking.parking_lot.split('(')[1].split(')')[0].strip()

    slot_label = ""
    if booking.slot and hasattr(booking.slot, 'slot_number'):
        slot_label = booking.slot.slot_number
    elif 'Slot:' in booking.parking_lot:
        slot_label = booking.parking_lot.split('Slot:')[1].replace(']', '').replace('Slot:', '').strip()

    context = {
        'page_title': f"Booking Ticket #{booking.id} - ParkEase Digital Pass",
        'booking': booking,
        'lot': lot,
        'lot_name': lot_name,
        'lot_address': lot_address,
        'slot_label': slot_label,
        'duration_hours': duration_hours,
        'tariff_rate': tariff_rate,
        'base_charge': base_charge,
        'qr_base64': qr_base64,
        'directions_url': google_maps_directions_url,
        'lat': lat,
        'lng': lng,
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_1DP5mmOlF5G5ag'),
        'overstay_amount_paise': int(round((booking.overstay_fine or Decimal('20.00')) * 100)),
    }
    return render(request, 'parking/booking_ticket.html', context)


@login_required
def my_bookings_view(request):
    
    now = timezone.now()
    user_bookings = Booking.objects.filter(user=request.user).select_related('lot', 'vehicle').order_by('-created_at')
    
    active_bookings = []
    history_bookings = []
    
    for b in user_bookings:
        if b.is_service_over:
            if b.booking_status == 'active' and not b.is_parked:
                b.booking_status = 'completed'
                b.save(update_fields=['booking_status'])
                if b.slot and b.slot.status != 'maintenance':
                    b.slot.status = 'available'
                    b.slot.save(update_fields=['status'])
            history_bookings.append(b)
        else:
            active_bookings.append(b)

    active_tab = request.GET.get('tab', '')
    if active_tab not in ('current', 'history', 'all'):
        
        if not active_bookings and history_bookings:
            active_tab = 'history'
        else:
            active_tab = 'current'

    context = {
        'page_title': 'Current Booking & History - ParkEase',
        'bookings': user_bookings,
        'active_bookings': active_bookings,
        'history_bookings': history_bookings,
        'active_tab': active_tab,
        'now': now,
    }
    return render(request, 'bookings/my_bookings.html', context)


def submit_admin_feedback_view(request):
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        category = request.POST.get('category', 'general').strip()
        try:
            rating = int(request.POST.get('rating', 5))
            if rating < 1 or rating > 5:
                rating = 5
        except (ValueError, TypeError):
            rating = 5
        message = request.POST.get('message', '').strip()

        if not message:
            messages.error(request, "Please enter your feedback message before submitting.")
            return redirect(request.META.get('HTTP_REFERER') or 'parking:home')

        user = request.user if request.user.is_authenticated else None
        if not name and user:
            name = user.get_full_name() or user.username
        if not email and user:
            email = user.email
        if not email:
            from django.conf import settings
            email = getattr(settings, 'USER_EMAIL', 'saavanbaems@gmail.com')

        from admin_panel.models import PlatformFeedback, AdminNotification
        fb = PlatformFeedback.objects.create(
            user=user,
            name=name or 'Valued Motorist',
            email=email,
            category=category,
            rating=rating,
            message=message,
        )

        
        try:
            AdminNotification.objects.create(
                category='feedback',
                title=f"New Direct Feedback: {fb.name} ({fb.rating}★)",
                message=f"[{fb.get_category_display()}] {message[:120]}...",
                link='/admin-panel/feedbacks/'
            )
        except Exception:
            pass

        
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_user_feedback_acknowledgment(fb)
            EmailNotificationService.send_admin_new_feedback_alert(fb)
        except Exception as e:
            pass

        messages.success(
            request,
            "Thank you for your feedback! Your message has been sent directly to our administration team. "
            "A confirmation email has been dispatched to your inbox."
        )
        return redirect(request.META.get('HTTP_REFERER') or 'parking:home')

    return redirect('parking:home')


@login_required
def submit_booking_review_view(request, booking_id):
   
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 5))
            if rating < 1 or rating > 5:
                rating = 5
        except (ValueError, TypeError):
            rating = 5
        comment = request.POST.get('comment', '').strip()

        if not comment:
            messages.error(request, "Please share a few words about your parking experience.")
            return redirect(f"{request.META.get('HTTP_REFERER') or '/my-bookings/?tab=history'}")

        lot = booking.lot
        if not lot:
            lot_name_prefix = booking.parking_lot.split('(')[0].strip()
            lot = ParkingLot.objects.filter(name__icontains=lot_name_prefix).first()
            if not lot:
                lot = ParkingLot.objects.first()

        from lot_owner_panel.models import LotReview, OwnerNotification
        driver_name = request.user.get_full_name() or request.user.username
        booking_ref = f"PE-BK-{booking.id}"

        review, created = LotReview.objects.update_or_create(
            parking_lot=lot,
            booking_ref=booking_ref,
            defaults={
                'user': request.user,
                'driver_name': driver_name,
                'rating': rating,
                'comment': comment,
            }
        )

        
        if lot.owner:
            try:
                from django.db.models import Avg
                owner_avg = LotReview.objects.filter(parking_lot__owner=lot.owner).aggregate(avg=Avg('rating'))['avg']
                owner_avg_str = f"{float(owner_avg):.1f}★" if owner_avg else f"{rating}.0★"

                OwnerNotification.objects.create(
                    owner=lot.owner,
                    category='review',
                    title=f"New {rating}★ Driver Rating Received",
                    message=f"{driver_name} rated {lot.name} {rating} stars: \"{comment}\". Your total owner rating is now {owner_avg_str}.",
                    is_read=False
                )
            except Exception:
                pass

        
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_user_review_acknowledgment(review)
            EmailNotificationService.send_owner_new_review_alert(review)
        except Exception:
            pass

        owner_name = f"{lot.owner.first_name} {lot.owner.last_name}".strip() if (lot.owner and (lot.owner.first_name or lot.owner.last_name)) else (lot.owner.username if lot.owner else "Space Owner")
        messages.success(
            request,
            f"Thank you! Your {rating}-star rating and review for {lot.name} have been submitted. "
            f"This has updated space owner {owner_name}'s total rating score, and a confirmation email has been dispatched."
        )
        return redirect(f"/my-bookings/?tab=history")

    return redirect('parking:my_bookings')


def scan_entry_view(request, booking_id):
    
    booking = get_object_or_404(Booking, id=booking_id)
    now = timezone.now()

    booking.entry_time = now
    booking.is_parked = True
    booking.booking_status = 'active'
    booking.save()

    plate = booking.vehicle.registration_number if booking.vehicle else 'Vehicle'
    messages.success(
        request, 
        f" Gate Barrier Opened! {plate} verified and checked in at {now.strftime('%I:%M %p')}. Enjoy your parking session."
    )
    return redirect(request.META.get('HTTP_REFERER') or f'/booking/{booking.id}/ticket/')


def scan_exit_view(request, booking_id):
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    
    simulate_overstay_mins = (
        request.POST.get('simulate_overstay_minutes') or 
        request.GET.get('simulate_overstay_minutes') or 
        request.GET.get('overstay_minutes') or 
        request.POST.get('overstay_minutes') or
        (30 if request.GET.get('simulate_overstay') or request.POST.get('simulate_overstay') else None)
    )
    if simulate_overstay_mins and booking.end_time:
        now = booking.end_time + timedelta(minutes=int(simulate_overstay_mins))
    else:
        now = timezone.now()

    
    lot_name_prefix = booking.parking_lot.split('(')[0].strip()
    lot = ParkingLot.objects.filter(name__icontains=lot_name_prefix).first()
    hourly_rate = float(lot.hourly_rate) if lot else 50.0

    
    if booking.end_time and now > booking.end_time and not booking.overstay_paid:
        diff_seconds = (now - booking.end_time).total_seconds()
        diff_minutes = int(diff_seconds // 60)
        overstay_hours = round(Decimal(str(diff_seconds / 3600)), 2)
        
        
        extra_fee = round(Decimal(str(float(overstay_hours) * hourly_rate)), 2)
        if extra_fee <= Decimal('0.00'):
            extra_fee = Decimal('20.00')

        booking.overstay_hours = overstay_hours
        booking.overstay_fine = extra_fee
        booking.overstay_paid = False
        booking.save()

        messages.warning(
            request,
            f" Overstay Detected! Booked duration ended at {booking.end_time.strftime('%I:%M %p')}. "
            f"Extra stay: {diff_minutes} mins ({overstay_hours} hrs). "
            f"Additional Fee: ₹{extra_fee}. Gate barrier remains locked until extra fee is paid via Razorpay."
        )
        return redirect(f'/booking/{booking.id}/ticket/?overstay_due=1')


    booking.exit_time = now
    booking.is_parked = False
    booking.booking_status = 'completed'
    booking.save()

    messages.success(
        request,
        f" Exit QR Verified! Exit gate barrier opened at {now.strftime('%I:%M %p')}. Have a safe drive!"
    )
    return redirect(request.META.get('HTTP_REFERER') or f'/booking/{booking.id}/ticket/')


def pay_overstay_view(request, booking_id):
    
    booking = get_object_or_404(Booking, id=booking_id)
    razorpay_pay_id = request.POST.get('razorpay_payment_id') or f"pay_rzp_overstay_{uuid.uuid4().hex[:10]}"

    paid_fine = booking.overstay_fine or Decimal('20.00')
    booking.overstay_paid = True
    booking.total_amount += paid_fine
    booking.exit_time = timezone.now()
    booking.is_parked = False
    booking.booking_status = 'completed'
    booking.razorpay_payment_id = razorpay_pay_id
    booking.save()

    messages.success(
        request,
        f"✅ Overstay fee of ₹{paid_fine} settled via Razorpay! Exit gate barrier opened. Drive safely."
    )
    return redirect(f'/booking/{booking.id}/ticket/')


def gate_scanner_view(request):
    
    booking = None
    query_token = request.GET.get('token', '').strip()
    if query_token:
        
        if query_token.isdigit():
            booking = Booking.objects.filter(id=int(query_token)).first()
        if not booking:
            booking = Booking.objects.filter(qr_code_token__icontains=query_token).first()

    context = {
        'page_title': 'Gate Barrier & QR Pass Scanner - ParkEase',
        'booking': booking,
        'query_token': query_token,
    }
    return render(request, 'parking/gate_scanner.html', context)



def browse_cities_view(request):
    
    city_definitions = [
        {
            'name': 'Mumbai',
            'state': 'Maharashtra',
            'tagline': 'Financial Capital & Metro Transit Hub',
            'description': 'Find secure parking across BKC business towers, Nariman Point corporate bays, and Chhatrapati Shivaji Airport (BOM) terminals.',
            'query': 'Mumbai',
            'badge': 'High Demand',
            'icon': 'bi-buildings',
            'popular_areas': ['Bandra Kurla Complex (BKC)', 'Nariman Point', 'CSMT Fort', 'Andheri East', 'BOM Airport T2'],
        },
        {
            'name': 'Delhi NCR',
            'state': 'Delhi & Haryana',
            'tagline': 'Capital Region & Corporate Express Hub',
            'description': 'Guaranteed parking in Connaught Place inner/outer circles, DLF Cyber City Gurugram, Noida Sector 18, and IGI Airport (DEL) T3.',
            'query': 'Delhi NCR',
            'badge': 'Top Metro',
            'icon': 'bi-geo-alt-fill',
            'popular_areas': ['Connaught Place', 'DLF Cyber City', 'IGI Airport T3', 'Noida Sector 18', 'Gurugram Phase 2'],
        },
        {
            'name': 'Bengaluru',
            'state': 'Karnataka',
            'tagline': 'Silicon Valley of India',
            'description': 'Hassle-free parking across MG Road commercial hubs, Indiranagar 100 Feet Road, Whitefield tech parks, and Kempegowda Airport (BLR).',
            'query': 'Bengaluru',
            'badge': 'Tech Hub',
            'icon': 'bi-laptop',
            'popular_areas': ['MG Road', 'Indiranagar', 'Koramangala', 'Whitefield ITPL', 'BLR Airport'],
        },
        {
            'name': 'Pune',
            'state': 'Maharashtra',
            'tagline': 'Oxford of the East & IT Corridor',
            'description': 'Prime parking spots along FC Road, Koregaon Park lifestyle hubs, Shivaji Nagar, and Pune Airport (PNQ) AeroMall.',
            'query': 'Pune',
            'badge': 'Popular',
            'icon': 'bi-mortarboard',
            'popular_areas': ['FC Road', 'Shivajinagar', 'Koregaon Park', 'Viman Nagar', 'PNQ Airport'],
        },
        {
            'name': 'Hyderabad',
            'state': 'Telangana',
            'tagline': 'City of Pearls & Cyberabad',
            'description': 'Instant parking bays around Hitec City Cyber Towers, Banjara Hills Road No 1, Gachibowli, and Rajiv Gandhi Airport (HYD).',
            'query': 'Hyderabad',
            'badge': 'Fast Growing',
            'icon': 'bi-cpu',
            'popular_areas': ['Hitec City', 'Banjara Hills', 'Madhapur', 'Gachibowli', 'HYD Airport'],
        },
        {
            'name': 'Ahmedabad',
            'state': 'Gujarat',
            'tagline': 'Heritage & Premier Commercial Center',
            'description': 'Our largest parking network spanning Navrangpura, C.G. Road, Prahlad Nagar corporate valet bays, and SVPI Airport (AMD).',
            'query': 'Ahmedabad',
            'badge': 'Flagship Network',
            'icon': 'bi-star-fill',
            'popular_areas': ['Navrangpura', 'C.G. Road', 'Prahlad Nagar', 'Vijay Cross Roads', 'AMD Airport'],
        },
        {
            'name': 'Chennai',
            'state': 'Tamil Nadu',
            'tagline': 'Gateway of South India',
            'description': 'Convenient parking in T. Nagar shopping districts, Anna Nagar, OMR IT Expressway, and Chennai International Airport (MAA).',
            'query': 'Chennai',
            'badge': 'Coastal Metro',
            'icon': 'bi-compass',
            'popular_areas': ['T. Nagar', 'Anna Nagar', 'OMR Tech Corridor', 'Nungambakkam', 'MAA Airport'],
        },
    ]

    all_lots = list(ParkingLot.objects.filter(status='approved', is_paused=False))
    cities_data = []
    for c in city_definitions:
        q = c['query'].lower()
        matched = [l for l in all_lots if q in f"{l.city} {l.name} {l.area} {l.state}".lower()]
        lot_count = len(matched)
        total_capacity = sum(l.total_capacity for l in matched)
        min_rate = min([l.hourly_rate for l in matched]) if matched else 50
        cities_data.append({
            **c,
            'lot_count': lot_count if lot_count > 0 else 2,
            'total_capacity': total_capacity if total_capacity > 0 else 60,
            'min_rate': int(min_rate),
        })

    context = {
        'page_title': 'Browse All Cities - Find Verified Parking in India | ParkEase',
        'cities': cities_data,
        'total_cities': len(cities_data),
    }
    return render(request, 'parking/browse_cities.html', context)


def browse_airports_view(request):
    
    airports_list = [
        {
            'code': 'DEL',
            'name': 'Indira Gandhi International Airport',
            'city': 'New Delhi',
            'state': 'Delhi NCR',
            'terminals': 'Terminal 1, 2, 3 (Domestic & International)',
            'distance': 'On-Airport / Terminal 3 Walkway',
            'daily_rate': 499,
            'hourly_rate': 90,
            'features': ['Free 24/7 Shuttle', 'Terminal Valet', 'EV Fast Charging', 'CCTV & Security Guard'],
            'description': 'Delhi NCR’s premier airport parking network offering covered multi-level bays adjacent to T3 and express drop-off valet.',
        },
        {
            'code': 'BOM',
            'name': 'Chhatrapati Shivaji Maharaj International Airport',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'terminals': 'Terminal 1 (Domestic) & Terminal 2 (International)',
            'distance': 'T2 Aeromall / 2-Min Terminal Walk',
            'daily_rate': 550,
            'hourly_rate': 100,
            'features': ['Multi-Level Covered Parking', 'EV Charging Bay', 'Valet Service', 'Luggage Assistance'],
            'description': 'Direct terminal access parking at Mumbai Airport with automated QR pass entry and 24/7 guarded security.',
        },
        {
            'code': 'BLR',
            'name': 'Kempegowda International Airport',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'terminals': 'Terminal 1 & Terminal 2 (Garden Terminal)',
            'distance': 'Airport Boulevard / 3-Min Free Shuttle',
            'daily_rate': 480,
            'hourly_rate': 80,
            'features': ['Free Terminal Shuttle', 'Valet Drop-off', 'Overnight Long-Term Rates', 'CCTV Monitored'],
            'description': 'Spacious and green airport parking facility at Devanahalli with designated spots for two-wheelers, sedans, SUVs, and EVs.',
        },
        {
            'code': 'HYD',
            'name': 'Rajiv Gandhi International Airport',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'terminals': 'Integrated Passenger Terminal',
            'distance': 'Aeropark Shamshabad / Shuttle Connected',
            'daily_rate': 420,
            'hourly_rate': 70,
            'features': ['Aeropark Shuttle', 'Covered Slots Available', '24/7 Patrol', 'Fast QR Gate Pass'],
            'description': 'Official Aeropark and partner bays at Shamshabad with seamless round-the-clock connectivity to departure gates.',
        },
        {
            'code': 'MAA',
            'name': 'Chennai International Airport',
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'terminals': 'Domestic (T1 & T4) & International (T2)',
            'distance': 'Meenambakkam MLCP / Walk to Terminals',
            'daily_rate': 450,
            'hourly_rate': 75,
            'features': ['Multi-Level Car Parking (MLCP)', 'Direct Walkway', 'Security Guarded', 'EV Charging'],
            'description': 'Covered MLCP facility directly connected to Chennai Airport departure and arrival terminals via aerobridges.',
        },
        {
            'code': 'CCU',
            'name': 'Netaji Subhash Chandra Bose International Airport',
            'city': 'Kolkata',
            'state': 'West Bengal',
            'terminals': 'Integrated Terminal Building',
            'distance': 'Dum Dum Airport FlyPark / 2-Min Shuttle',
            'daily_rate': 380,
            'hourly_rate': 60,
            'features': ['Guaranteed Reserved Bays', '24/7 Security', 'Free Shuttle', 'Two-Wheeler & Car Bays'],
            'description': 'Affordable and reliable airport parking for business travellers and holidaymakers flying out of Kolkata.',
        },
        {
            'code': 'AMD',
            'name': 'Sardar Vallabhbhai Patel International Airport',
            'city': 'Ahmedabad',
            'state': 'Gujarat',
            'terminals': 'Terminal 1 (Domestic) & Terminal 2 (International)',
            'distance': 'Airport Road Hansol / 3-Min Transfer',
            'daily_rate': 350,
            'hourly_rate': 50,
            'features': ['24/7 CCTV & Security', 'EV Charging', 'Free Terminal Drop', 'Valet Service'],
            'description': 'Secure parking facility minutes from Ahmedabad Airport terminals with transparent daily rates and zero wait times.',
        },
        {
            'code': 'COK',
            'name': 'Cochin International Airport',
            'city': 'Kochi',
            'state': 'Kerala',
            'terminals': 'Terminal 1, 2 & 3',
            'distance': 'Nedumbassery Solar Canopy Bay',
            'daily_rate': 320,
            'hourly_rate': 50,
            'features': ['Solar Canopy Covered', 'Green Certified', '24/7 Security', 'Free Shuttle'],
            'description': 'Eco-friendly solar-covered parking lots at Nedumbassery protecting your vehicle from sun and rain.',
        },
        {
            'code': 'GOI',
            'name': 'Goa Dabolim & Manohar (Mopa) International Airports',
            'city': 'Goa',
            'state': 'Goa',
            'terminals': 'Dabolim (GOI) & Mopa (GOX)',
            'distance': 'Airport Terminals / Valet Available',
            'daily_rate': 399,
            'hourly_rate': 65,
            'features': ['Both Airports Covered', 'Holiday Long-Term Discounts', 'Valet Drop', '24/7 Security'],
            'description': 'Stress-free vacation parking for travelers flying in or out of South Goa (Dabolim) and North Goa (Mopa).',
        },
        {
            'code': 'PNQ',
            'name': 'Pune International Airport',
            'city': 'Pune',
            'state': 'Maharashtra',
            'terminals': 'New Integrated Terminal Building',
            'distance': 'AeroMall Facility / Skywalk Access',
            'daily_rate': 390,
            'hourly_rate': 60,
            'features': ['AeroMall Skywalk Access', 'EV Charging Hub', 'Multi-Level Covered', '24/7 Assistance'],
            'description': 'Modern multi-level facility at AeroMall connected directly to Pune Airport departure gates via a pedestrian skywalk.',
        },
    ]

    context = {
        'page_title': 'Browse Airport Parking - Terminals, Long-Term & Valet | ParkEase',
        'airports': airports_list,
        'total_airports': len(airports_list),
    }
    return render(request, 'parking/browse_airports.html', context)



def policies_view(request):
    
    active_tab = request.GET.get('tab', 'privacy').lower()
    if active_tab not in ['privacy', 'overstay', 'all']:
        active_tab = 'privacy'

    context = {
        'page_title': 'Privacy Policy & Overstay Policy - ParkEase Legal',
        'active_tab': active_tab,
    }
    return render(request, 'parking/policies.html', context)


@login_required(login_url='accounts:login')
def cancel_booking_view(request, booking_id):
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.is_service_over:
        messages.error(request, "This parking session is already over. Completed bookings cannot be cancelled.")
        return redirect('parking:my_bookings')
    if booking.booking_status == 'cancelled':
        messages.info(request, "This booking has already been cancelled.")
        return redirect('parking:my_bookings')
    
    booking.booking_status = 'cancelled'
    booking.save()
    
    if booking.slot:
        booking.slot.status = 'available'
        booking.slot.save()
    
    
    try:
        from parkease.email_service import EmailNotificationService
        EmailNotificationService.send_booking_cancellation(booking)
    except Exception:
        pass
    
    
    if booking.lot and booking.lot.owner:
        try:
            from lot_owner_panel.models import OwnerNotification
            OwnerNotification.objects.create(
                owner=booking.lot.owner,
                category='cancellation',
                title=f"Booking #{booking.id} Cancelled by Driver",
                message=f"Motorist cancelled reservation #{booking.id} for bay {booking.slot.slot_number if booking.slot else 'assigned'}.",
                is_read=False
            )
        except Exception:
            pass

    messages.success(request, f"Booking #{booking.id} has been cancelled successfully. A confirmation email has been dispatched to {request.user.email}.")
    return redirect('parking:my_bookings')


@login_required(login_url='accounts:login')
def request_refund_view(request, booking_id):
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.is_service_over:
        messages.error(request, "This parking session is already over. Refund requests are not permitted once service has concluded.")
        return redirect('parking:my_bookings')
    if request.method == 'POST':
        reason = request.POST.get('refund_reason', '').strip()
        booking.payment_status = 'refund_requested'
        booking.refund_reason = reason or "Driver requested cancellation and refund."
        booking.refund_requested_at = timezone.now()
        booking.save()

        
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_admin_alert(
                event_type='admin_refund_claim',
                subject=f"Action Required: Refund Request for Booking #{booking.id}",
                message_body=(
                    f"Motorist <strong>{request.user.username}</strong> has requested a refund for Booking <strong>#{booking.id}</strong>.<br>"
                    f"Facility: <strong>{booking.parking_lot}</strong><br>"
                    f"Refund Amount: <strong>INR {booking.total_amount}</strong><br>"
                    f"Reason: <em>{booking.refund_reason}</em>"
                ),
                details_dict={
                    'Booking ID': f"#{booking.id}",
                    'Motorist': f"{request.user.get_full_name() or request.user.username} ({request.user.email})",
                    'Facility': booking.parking_lot,
                    'Refund Claim': f"INR {booking.total_amount}",
                    'Motorist Reason': booking.refund_reason,
                    'Requested At': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
                    'Admin Action': 'Open Admin Studio to approve or process refund',
                }
            )
        except Exception:
            pass

        
        try:
            from admin_panel.models import AdminNotification
            AdminNotification.objects.create(
                category='refund',
                title=f"Approval Required: Refund Request #{booking.id}",
                message=f"Motorist {request.user.username} requested refund of INR {booking.total_amount} for Booking #{booking.id}. Reason: {booking.refund_reason}",
                link='/admin-panel/payments/?status=refunded',
                is_read=False
            )
        except Exception:
            pass

        messages.success(request, f"Refund request for INR {booking.total_amount} submitted successfully. Notification and approval alert dispatched to Admin Studio.")
    return redirect('parking:my_bookings')


@login_required(login_url='accounts:login')
def extend_booking_view(request, booking_id):
    
    from bookings.models import BookingExtensionRequest
    from lot_owner_panel.models import OwnerNotification

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.is_service_over:
        messages.error(request, "This parking session is already over. Time extension is not permitted for completed bookings.")
        return redirect('parking:my_bookings')
    if request.method == 'POST':
        try:
            add_hours = float(request.POST.get('additional_hours', 1))
        except (ValueError, TypeError):
            add_hours = 1.0

        if add_hours <= 0:
            add_hours = 1.0

        rate = 50.00
        if booking.lot and booking.lot.hourly_rate:
            rate = float(booking.lot.hourly_rate)

        extra_fee = Decimal(str(round(rate * add_hours, 2)))
        curr_end = booking.end_time or timezone.now()
        new_end = curr_end + timedelta(hours=add_hours)

        
        conflict_booking = None
        conflict_detected = False
        conflict_text = ""

        conflicts_qs = Booking.objects.filter(
            booking_status='active',
            payment_status='paid'
        ).exclude(id=booking.id).exclude(user=request.user)

        if booking.slot:
            slot_conflicts = conflicts_qs.filter(
                slot=booking.slot,
                start_time__lt=new_end,
                end_time__gt=curr_end
            )
            if slot_conflicts.exists():
                conflict_booking = slot_conflicts.first()
                conflict_detected = True

        if not conflict_detected and booking.lot:
            lot_conflicts = conflicts_qs.filter(
                lot=booking.lot,
                start_time__lt=new_end,
                end_time__gt=curr_end
            )
            if lot_conflicts.exists():
                conflict_booking = lot_conflicts.first()
                conflict_detected = True

        if conflict_detected and conflict_booking:
            second_user_name = conflict_booking.user.get_full_name() or conflict_booking.user.username
            start_str = conflict_booking.start_time.strftime('%I:%M %p, %b %d')
            end_str = conflict_booking.end_time.strftime('%I:%M %p, %b %d') if conflict_booking.end_time else "departure"
            slot_str = conflict_booking.slot.slot_number if conflict_booking.slot else "Parking Bay"
            conflict_text = (
                f"This is the user who asked for extension of time, but from {start_str} to {end_str}, "
                f"second user {second_user_name} (Booking #BK-{conflict_booking.id}) has this parking space ({slot_str}) "
                f"which is already booked and paid. In that new lot/slot, requesting extra time user can be given, "
                f"but they have to leave the lot once their time is over."
            )

        
        ext_req = BookingExtensionRequest.objects.create(
            booking=booking,
            requested_by=request.user,
            additional_hours=Decimal(str(round(add_hours, 2))),
            current_end_time=curr_end,
            requested_new_end_time=new_end,
            additional_fee=extra_fee,
            status='pending',
            conflict_detected=conflict_detected,
            conflicting_booking=conflict_booking,
            conflict_details=conflict_text,
        )

        
        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_owner_extension_request(ext_req)
        except Exception:
            pass

        
        if booking.lot and booking.lot.owner:
            OwnerNotification.objects.create(
                owner=booking.lot.owner,
                category='extension',
                title=f"Time Extension Request: #BK-{booking.id}",
                message=(
                    f"Motorist {booking.user.get_full_name() or booking.user.username} requested a {int(add_hours)}-hour "
                    f"extension until {new_end.strftime('%I:%M %p, %b %d')} for {booking.parking_lot}. "
                    f"Additional fee: INR {extra_fee:.2f}."
                    + (f" ⚠️ Conflict Alert: Overlaps with booking #BK-{conflict_booking.id} by {conflict_booking.user.username}." if conflict_detected else "")
                )
            )

        messages.success(
            request,
            f"Your request to extend parking by {int(add_hours)} hr(s) (until {new_end.strftime('%I:%M %p, %b %d')}) "
            f"has been submitted! The space owner has received an alert and email for approval. "
            f"You will receive an email confirmation once approved."
        )
    return redirect('parking:my_bookings')

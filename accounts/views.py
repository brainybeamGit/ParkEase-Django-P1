import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .models import UserProfile, Vehicle, normalize_registration_number


def validate_name(name, field_label="Name"):
    val = (name or '').strip()
    if not val:
        return False, f"{field_label} is required."
    if len(val) < 2:
        return False, f"{field_label} must be at least 2 characters long."
    if len(val) > 30:
        return False, f"{field_label} cannot exceed 30 characters."
    if not re.match(r"^[A-Za-z\s'\-]+$", val):
        return False, f"{field_label} can only contain alphabetic letters (no numbers or special symbols)."
    return True, val


def validate_email_address(email):
    raw = (email or '').strip()
    if not raw:
        return False, "Email address is required."
    pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    if not re.match(pattern, raw, re.IGNORECASE):
        return False, "Email address must be a valid Gmail address ending with '@gmail.com' (e.g. user@gmail.com)."
    user_part = raw.split('@')[0]
    if len(user_part) < 3:
        return False, "Email username must be at least 3 characters before @gmail.com."
    if len(raw) > 60:
        return False, "Email address is too long (maximum 60 characters)."
    return True, raw.lower()


def validate_mobile_number(mobile):
    raw = (mobile or '').strip()
    if not raw:
        return False, "Mobile phone number is required."
    cleaned = re.sub(r'[\s\-\(\)]+', '', raw)
    digits_only = re.sub(r'\D', '', cleaned)
    if digits_only.startswith('91') and len(digits_only) == 12:
        digits_only = digits_only[2:]
    elif digits_only.startswith('0') and len(digits_only) == 11:
        digits_only = digits_only[1:]
    if len(digits_only) < 10:
        return False, f"Mobile number must be exactly 10 digits (you entered {len(digits_only)} digits; minimum 10 required)."
    if len(digits_only) > 10:
        return False, f"Mobile number must be exactly 10 digits (you entered {len(digits_only)} digits; maximum 10 allowed)."
    if not re.match(r'^[6-9]\d{9}$', digits_only):
        return False, "Mobile number must be a valid 10-digit number starting with 6, 7, 8, or 9."
    formatted = f"+91 {digits_only[:5]} {digits_only[5:]}"
    return True, formatted


def validate_password_strength(password):
    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, f"Password is too short (minimum 6 characters required, you entered {len(password)})."
    if len(password) > 15:
        return False, f"Password is too long (maximum 15 characters allowed, you entered {len(password)})."
    return True, password


def validate_registration_number(raw_reg):
    normalized = normalize_registration_number(raw_reg)
    if not normalized:
        return False, "Vehicle registration number is required."
    compact = re.sub(r'\s+', '', normalized)
    if len(compact) < 4:
        return False, "Registration number is too short (minimum 4 characters)."
    if len(compact) > 16:
        return False, "Registration number is too long (maximum 16 characters)."
    if not re.match(r'^[A-Z0-9\s\-]+$', normalized):
        return False, "Registration number contains invalid characters. Use letters, numbers, and spaces."
    has_digit = any(c.isdigit() for c in compact)
    has_letter = any(c.isalpha() for c in compact)
    if not (has_digit and has_letter):
        return False, "Registration number must contain both letters and digits (e.g. DL 01 AB 1234)."
    return True, normalized


def generate_unique_username(email, first_name):
    base = email.split('@')[0] if email else first_name.lower().replace(' ', '')
    base = re.sub(r'[^a-zA-Z0-9_]', '', base)
    if not base or len(base) < 3:
        base = "driver"
    username = base
    counter = 1
    while User.objects.filter(username__iexact=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


def login_view(request):
    if request.user.is_authenticated:
        return redirect('parking:home')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        if not identifier or not password:
            messages.error(request, "Please enter both username/email and password.")
            return render(request, 'accounts/login.html', {
                'identifier': identifier,
                'next': next_url,
            })

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            user_candidates = list(User.objects.filter(email__iexact=identifier))
            if not user_candidates and identifier.lower() in ('user', 'user@gmail.com'):
                user_candidates = list(User.objects.filter(username__iexact='user@gmail.com'))
            elif not user_candidates and identifier.lower() in ('owner', 'owner@gmail.com'):
                user_candidates = list(User.objects.filter(username__iexact='owner@gmail.com'))
            elif not user_candidates and identifier.lower() == 'admin':
                user_candidates = list(User.objects.filter(username__iexact='admin'))
            
            for candidate in user_candidates:
                user = authenticate(request, username=candidate.username, password=password)
                if user is not None:
                    break

        if user is not None:
            if user.is_active:
                login(request, user)
                if remember_me:
                    request.session.set_expiry(1209600)  # 14 days
                else:
                    request.session.set_expiry(0)

                display_name = user.first_name if user.first_name else user.username
                messages.success(request, f"Welcome back, {display_name}!")


                try:
                    from parkease.email_service import EmailNotificationService
                    client_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
                    if hasattr(user, 'lot_owner_profile') or (hasattr(user, 'profile') and user.profile.role == 'owner'):
                        EmailNotificationService.send_owner_login_alert(user, ip=client_ip)
                    else:
                        EmailNotificationService.send_user_login_alert(user, ip=client_ip)
                except Exception:
                    pass

                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)

                
                if hasattr(user, 'lot_owner_profile') or (hasattr(user, 'profile') and user.profile.role == 'owner'):
                    return redirect('lot_owner_panel:dashboard')
                elif user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'admin'):
                    return redirect('admin_panel:dashboard')
                return redirect('parking:home')
            else:
                messages.error(request, "This account has been deactivated. Please contact support.")
        else:
            messages.error(request, "Invalid username/email or password. Please verify your credentials.")

        return render(request, 'accounts/login.html', {
            'identifier': identifier,
            'next': next_url,
        })

    return render(request, 'accounts/login.html', {
        'next': next_url,
    })


def register_view(request):

    if request.user.is_authenticated:
        return redirect('parking:home')

    if request.method == 'POST':

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')


        vehicle_reg = request.POST.get('vehicle_reg', '').strip()
        vehicle_type = request.POST.get('vehicle_type', 'car').strip()
        other_vehicle_type = request.POST.get('other_vehicle_type', '').strip()
        vehicle_make = request.POST.get('vehicle_make', '').strip()
        vehicle_model = request.POST.get('vehicle_model', '').strip()
        is_ev = bool(request.POST.get('is_ev'))
        agree_terms = bool(request.POST.get('agree_terms'))

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'mobile_number': mobile_number,
            'vehicle_reg': vehicle_reg,
            'vehicle_type': vehicle_type,
            'other_vehicle_type': other_vehicle_type,
            'vehicle_make': vehicle_make,
            'vehicle_model': vehicle_model,
            'is_ev': is_ev,
            'agree_terms': agree_terms,
        }

        fn_valid, fn_result = validate_name(first_name, "First Name")
        if not fn_valid:
            messages.error(request, fn_result)
            return render(request, 'accounts/register.html', form_data)
        first_name = fn_result

        ln_valid, ln_result = validate_name(last_name, "Last Name")
        if not ln_valid:
            messages.error(request, ln_result)
            return render(request, 'accounts/register.html', form_data)
        last_name = ln_result

        em_valid, em_result = validate_email_address(email)
        if not em_valid:
            messages.error(request, em_result)
            return render(request, 'accounts/register.html', form_data)
        email = em_result

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, f"An account with email '{email}' already exists. Please log in or use another email.")
            return render(request, 'accounts/register.html', form_data)

        mobile_valid, mobile_result = validate_mobile_number(mobile_number)
        if not mobile_valid:
            messages.error(request, mobile_result)
            return render(request, 'accounts/register.html', form_data)

        pwd_valid, pwd_result = validate_password_strength(password)
        if not pwd_valid:
            messages.error(request, pwd_result)
            return render(request, 'accounts/register.html', form_data)

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter identical passwords.")
            return render(request, 'accounts/register.html', form_data)


        reg_valid, reg_result = validate_registration_number(vehicle_reg)
        if not reg_valid:
            messages.error(request, reg_result)
            return render(request, 'accounts/register.html', form_data)

        allowed_types = ['two_wheeler', 'car', 'suv', 'other']
        if vehicle_type not in allowed_types:
            vehicle_type = 'car'

        if vehicle_type == 'other' and other_vehicle_type:
            if not vehicle_make:
                vehicle_make = other_vehicle_type
            else:
                vehicle_model = f"{vehicle_model} ({other_vehicle_type})".strip()

        if not agree_terms:
            messages.error(request, "You must agree to the Terms and Conditions and Privacy Policy.")
            return render(request, 'accounts/register.html', form_data)


        username = generate_unique_username(email, first_name)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )


        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.mobile_number = mobile_result
        profile.save()


        vehicle = Vehicle.objects.create(
            user=user,
            registration_number=reg_result,
            vehicle_type=vehicle_type,
            make=vehicle_make,
            model=vehicle_model,
            is_ev=is_ev,
            is_primary=True
        )


        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_user_welcome(user)
        except Exception:
            pass


        login(request, user)
        messages.success(
            request, 
            f"Welcome to ParkEase, {first_name}! Your account and primary vehicle ({vehicle.registration_number}) are registered."
        )
        return redirect('accounts:vehicles')

    return render(request, 'accounts/register.html', {'vehicle_type': 'car'})


@login_required(login_url='accounts:login')
def vehicles_view(request):

    user_vehicles = request.user.vehicles.all()
    return render(request, 'accounts/vehicles.html', {
        'vehicles': user_vehicles,
    })


@login_required(login_url='accounts:login')
def add_vehicle_view(request):

    if request.method == 'POST':
        vehicle_reg = request.POST.get('vehicle_reg', '').strip()
        vehicle_type = request.POST.get('vehicle_type', 'car').strip()
        other_vehicle_type = request.POST.get('other_vehicle_type', '').strip()
        vehicle_make = request.POST.get('vehicle_make', '').strip()
        vehicle_model = request.POST.get('vehicle_model', '').strip()
        is_ev = bool(request.POST.get('is_ev'))
        is_primary = bool(request.POST.get('is_primary'))

        reg_valid, reg_result = validate_registration_number(vehicle_reg)
        if not reg_valid:
            messages.error(request, reg_result)
            return redirect('accounts:vehicles')

        allowed_types = ['two_wheeler', 'car', 'suv', 'other']
        if vehicle_type not in allowed_types:
            vehicle_type = 'car'

        if vehicle_type == 'other' and other_vehicle_type:
            if not vehicle_make:
                vehicle_make = other_vehicle_type
            else:
                vehicle_model = f"{vehicle_model} ({other_vehicle_type})".strip()

        if not request.user.vehicles.exists():
            is_primary = True

        veh = Vehicle.objects.create(
            user=request.user,
            registration_number=reg_result,
            vehicle_type=vehicle_type,
            make=vehicle_make,
            model=vehicle_model,
            is_ev=is_ev,
            is_primary=is_primary
        )

        try:
            from parkease.email_service import EmailNotificationService
            EmailNotificationService.send_vehicle_added(request.user, veh)
        except Exception:
            pass

        messages.success(request, f"Vehicle '{reg_result}' added successfully. Confirmation email sent.")
        next_url = request.GET.get('next') or request.POST.get('next')
        return redirect(next_url or 'accounts:vehicles')

    return redirect('accounts:vehicles')


@login_required(login_url='accounts:login')
def set_primary_vehicle_view(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    vehicle.is_primary = True
    vehicle.save()
    messages.success(request, f"'{vehicle.registration_number}' is now your primary vehicle.")
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url or 'accounts:vehicles')


@login_required(login_url='accounts:login')
def delete_vehicle_view(request, vehicle_id):
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    was_primary = vehicle.is_primary
    reg_num = vehicle.registration_number
    vehicle.delete()

    if was_primary:
        next_primary = request.user.vehicles.first()
        if next_primary:
            next_primary.is_primary = True
            next_primary.save()

    messages.info(request, f"Vehicle '{reg_num}' has been removed from your account.")
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url or 'accounts:vehicles')


@login_required(login_url='accounts:login')
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    primary_vehicle = user.vehicles.filter(is_primary=True).first() or user.vehicles.first()
    vehicles = user.vehicles.all().order_by('-is_primary', '-created_at')
    vehicles_count = vehicles.count()
    bookings_count = user.bookings.count() if hasattr(user, 'bookings') else 0

    profile_context = {
        'profile': profile,
        'primary_vehicle': primary_vehicle,
        'vehicles': vehicles,
        'vehicles_count': vehicles_count,
        'bookings_count': bookings_count,
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            mobile_number = request.POST.get('mobile_number', '').strip()

            fn_valid, fn_result = validate_name(first_name, "First Name")
            if not fn_valid:
                messages.error(request, fn_result)
                return render(request, 'accounts/profile.html', profile_context)
            first_name = fn_result

            ln_valid, ln_result = validate_name(last_name, "Last Name")
            if not ln_valid:
                messages.error(request, ln_result)
                return render(request, 'accounts/profile.html', profile_context)
            last_name = ln_result

            if email:
                em_valid, em_result = validate_email_address(email)
                if not em_valid:
                    messages.error(request, em_result)
                    return render(request, 'accounts/profile.html', profile_context)
                if User.objects.filter(email__iexact=em_result).exclude(id=user.id).exists():
                    messages.error(request, f"An account with email '{em_result}' already exists.")
                    return render(request, 'accounts/profile.html', profile_context)
                user.email = em_result

            if mobile_number:
                mobile_valid, mobile_result = validate_mobile_number(mobile_number)
                if not mobile_valid:
                    messages.error(request, mobile_result)
                    return render(request, 'accounts/profile.html', profile_context)
                profile.mobile_number = mobile_result
            else:
                profile.mobile_number = ''

            user.first_name = first_name
            user.last_name = last_name
            user.save()
            profile.save()

            try:
                from parkease.email_service import EmailNotificationService
                EmailNotificationService.send_profile_updated(user, mobile=profile.mobile_number)
            except Exception:
                pass

            messages.success(request, "Your profile information has been updated successfully. A confirmation email has been sent.")
            return redirect('accounts:profile')

        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not current_password or not new_password or not confirm_password:
                messages.error(request, "Please fill in all password fields.")
                return render(request, 'accounts/profile.html', profile_context)

            if not user.check_password(current_password):
                messages.error(request, "Your current password is incorrect. If you have forgotten it, click 'Forgot password?' below.")
                return render(request, 'accounts/profile.html', profile_context)

            pwd_valid, pwd_result = validate_password_strength(new_password)
            if not pwd_valid:
                messages.error(request, pwd_result)
                return render(request, 'accounts/profile.html', profile_context)

            if new_password != confirm_password:
                messages.error(request, "New password and confirm password do not match.")
                return render(request, 'accounts/profile.html', profile_context)

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)

            try:
                from parkease.email_service import EmailNotificationService
                EmailNotificationService.send_password_reset_success(user)
            except Exception:
                pass

            messages.success(request, "Your password has been updated successfully. A confirmation email has been dispatched.")
            return redirect('accounts:profile')

        elif action == 'request_otp_reset':
            import random
            from datetime import timedelta
            from django.utils import timezone
            from .models import PasswordResetOTP
            from parkease.email_service import EmailNotificationService

            otp_code = f"{random.randint(100000, 999999)}"
            PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            PasswordResetOTP.objects.create(
                user=user,
                email=user.email,
                otp_code=otp_code,
                expires_at=timezone.now() + timedelta(minutes=10),
                is_used=False
            )
            EmailNotificationService.send_forgot_password_otp(user, otp_code)
            request.session['reset_email'] = user.email
            messages.success(request, f"A 6-digit password reset OTP has been dispatched to {user.email}.")
            return redirect(f"/accounts/verify-otp/?email={user.email}")

    return render(request, 'accounts/profile.html', profile_context)


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('parking:home')


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, "Please enter your registered email address.")
            return render(request, 'accounts/forgot_password.html')

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            user = User.objects.filter(username__iexact=email).first()
        if user:
            import random
            from datetime import timedelta
            from django.utils import timezone
            from .models import PasswordResetOTP
            from parkease.email_service import EmailNotificationService

            otp_code = f"{random.randint(100000, 999999)}"
            PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            PasswordResetOTP.objects.create(
                user=user,
                email=user.email,
                otp_code=otp_code,
                expires_at=timezone.now() + timedelta(minutes=10),
                is_used=False
            )
            EmailNotificationService.send_forgot_password_otp(user, otp_code)
            request.session['reset_email'] = user.email
            messages.success(request, f"A 6-digit verification OTP has been dispatched to {user.email}.")
            return redirect(f"/accounts/verify-otp/?email={user.email}")
        else:
            messages.error(request, f"No ParkEase account found with email '{email}'. Please check the spelling or register.")

    email_prefill = request.GET.get('email', '')
    return render(request, 'accounts/forgot_password.html', {'email': email_prefill})


def verify_password_otp_view(request):
    email = request.GET.get('email') or request.POST.get('email') or request.session.get('reset_email', '')

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not email:
            messages.error(request, "Session expired. Please restart the password reset process.")
            return redirect('accounts:forgot_password')

        if not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
            messages.error(request, "Please enter a valid 6-digit numeric OTP code.")
            return render(request, 'accounts/verify_password_otp.html', {'email': email})

        pwd_valid, pwd_result = validate_password_strength(new_password)
        if not pwd_valid:
            messages.error(request, pwd_result)
            return render(request, 'accounts/verify_password_otp.html', {'email': email})

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter identical passwords.")
            return render(request, 'accounts/verify_password_otp.html', {'email': email})

        from django.utils import timezone
        from .models import PasswordResetOTP
        from parkease.email_service import EmailNotificationService

        otp_record = PasswordResetOTP.objects.filter(
            email__iexact=email,
            otp_code=otp_code,
            is_used=False,
            expires_at__gte=timezone.now()
        ).first()

        if not otp_record:
            messages.error(request, "Invalid or expired 6-digit OTP code. Please request a new one.")
            return render(request, 'accounts/verify_password_otp.html', {'email': email})

        user = otp_record.user
        user.set_password(new_password)
        user.save()

        otp_record.is_used = True
        otp_record.save()

        EmailNotificationService.send_password_reset_success(user)

        if 'reset_email' in request.session:
            del request.session['reset_email']

        messages.success(request, "Your password has been successfully reset! Please sign in with your new credentials.")
        return redirect('accounts:login')

    if not email:
        return redirect('accounts:forgot_password')

    return render(request, 'accounts/verify_password_otp.html', {'email': email})


def resend_password_otp_view(request):
    email = request.GET.get('email') or request.session.get('reset_email', '')
    if not email:
        messages.error(request, "Please enter your email to request an OTP.")
        return redirect('accounts:forgot_password')

    user = User.objects.filter(email__iexact=email).first()
    if user:
        import random
        from datetime import timedelta
        from django.utils import timezone
        from .models import PasswordResetOTP
        from parkease.email_service import EmailNotificationService

        otp_code = f"{random.randint(100000, 999999)}"
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        PasswordResetOTP.objects.create(
            user=user,
            email=user.email,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_used=False
        )
        EmailNotificationService.send_forgot_password_otp(user, otp_code)
        messages.success(request, f"A fresh 6-digit OTP has been dispatched to {user.email}.")
    else:
        messages.error(request, "No account found with this email.")

    return redirect(f"/accounts/verify-otp/?email={email}")

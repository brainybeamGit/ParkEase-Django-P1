import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parkease.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from lot_owner_panel.models import ParkingLot, ParkingSlot
from decimal import Decimal

User = get_user_model()

def seed_data():
    print("[*] Seeding initial demo data for ParkEase...")

    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@parkease.com',
            'password': 'admin123',
            'first_name': 'Platform',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'username': 'owner@gmail.com',
            'email': 'owner@gmail.com',
            'password': 'owner123',
            'first_name': 'Space',
            'last_name': 'Owner',
            'is_staff': False,
            'is_superuser': False,
        },
        {
            'username': 'user@gmail.com',
            'email': 'user@gmail.com',
            'password': 'user123',
            'first_name': 'Savan',
            'last_name': 'Motorist',
            'is_staff': False,
            'is_superuser': False,
        }
    ]

    created_users = {}
    for u_info in users_data:
        u = User.objects.filter(username=u_info['username']).first()
        if not u:
            u = User.objects.create_user(
                username=u_info['username'],
                email=u_info['email'],
                password=u_info['password'],
                first_name=u_info['first_name'],
                last_name=u_info['last_name'],
            )
            u.is_staff = u_info['is_staff']
            u.is_superuser = u_info['is_superuser']
            u.save()
            print(f"  [+] Created user: {u_info['username']}")
        else:
            u.set_password(u_info['password'])
            u.is_staff = u_info['is_staff']
            u.is_superuser = u_info['is_superuser']
            u.save()
            print(f"  [+] Verified user: {u_info['username']}")
        created_users[u_info['username']] = u


    owner = created_users['owner@gmail.com']
    sample_lots = [
        {
            'name': 'Alpha Grand Mall Parking',
            'space_type': 'commercial',
            'street_address': 'Sarkhej - Gandhinagar Hwy, Vastrapur',
            'area': 'Vastrapur',
            'city': 'Ahmedabad',
            'state': 'Gujarat',
            'pin_code': '380015',
            'total_capacity': 45,
            'hourly_rate': Decimal('50.00'),
            'car_rate': Decimal('50.00'),
            'bike_rate': Decimal('20.00'),
            'suv_rate': Decimal('80.00'),
            'map_location': '23.0378, 72.5312',
            'available_services': 'CCTV, Security Guard, Covered Parking, EV Charger',
            'status': 'approved',
        },
        {
            'name': 'Vijay Cross Roads Smart Bay',
            'space_type': 'open_lot',
            'street_address': 'Near Passport Seva Kendra, Navrangpura',
            'area': 'Navrangpura',
            'city': 'Ahmedabad',
            'state': 'Gujarat',
            'pin_code': '380009',
            'total_capacity': 30,
            'hourly_rate': Decimal('60.00'),
            'car_rate': Decimal('60.00'),
            'bike_rate': Decimal('25.00'),
            'suv_rate': Decimal('90.00'),
            'map_location': '23.0456, 72.5489',
            'available_services': 'CCTV, Security Guard, Automatic ANPR Barrier',
            'status': 'approved',
        }
    ]

    for lot_info in sample_lots:
        lot, created = ParkingLot.objects.get_or_create(
            name=lot_info['name'],
            defaults={
                'owner': owner,
                'space_type': lot_info['space_type'],
                'street_address': lot_info['street_address'],
                'area': lot_info['area'],
                'city': lot_info['city'],
                'state': lot_info['state'],
                'pin_code': lot_info['pin_code'],
                'total_capacity': lot_info['total_capacity'],
                'hourly_rate': lot_info['hourly_rate'],
                'car_rate': lot_info['car_rate'],
                'bike_rate': lot_info['bike_rate'],
                'suv_rate': lot_info['suv_rate'],
                'map_location': lot_info['map_location'],
                'available_services': lot_info['available_services'],
                'status': lot_info['status'],
                'agreed_terms': True,
                'agreed_privacy': True,
                'confirmed_declaration': True,
            }
        )
        if created:
            print(f"  [+] Created parking lot: {lot.name}")
            zones = ['A', 'B']
            for z in zones:
                for s_num in range(1, 6):
                    ParkingSlot.objects.get_or_create(
                        parking_lot=lot,
                        zone=z,
                        slot_number=f"{z}-{s_num:02d}",
                        defaults={
                            'vehicle_category': 'car',
                            'status': 'available'
                        }
                    )
        else:
            print(f"  [+] Verified parking lot: {lot.name}")

    print("[+] Demo database seeding completed successfully!")

if __name__ == '__main__':
    seed_data()

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_password_otp_view, name='verify_password_otp'),
    path('resend-otp/', views.resend_password_otp_view, name='resend_password_otp'),

    
    path('vehicles/', views.vehicles_view, name='vehicles'),
    path('vehicles/add/', views.add_vehicle_view, name='add_vehicle'),
    path('vehicles/set-primary/<int:vehicle_id>/', views.set_primary_vehicle_view, name='set_primary_vehicle'),
    path('vehicles/delete/<int:vehicle_id>/', views.delete_vehicle_view, name='delete_vehicle'),
]

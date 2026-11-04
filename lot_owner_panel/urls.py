from django.urls import path
from . import views

app_name = 'lot_owner_panel'

urlpatterns = [
    
    path('login/', views.owner_login_view, name='login'),
    path('logout/', views.owner_logout_view, name='logout'),
    path('register/step1/', views.owner_register_step1_view, name='register_step1'),
    path('register/step2/', views.owner_register_step2_view, name='register_step2'),
    path('register/step3/', views.owner_register_step3_view, name='register_step3'),
    path('register/success/', views.owner_register_success_view, name='register_success'),

    
    path('', views.owner_dashboard_view, name='dashboard'),
    path('dashboard/', views.owner_dashboard_view, name='dashboard_alt'),

    
    path('parking-lots/', views.owner_parking_lots_view, name='parking_lots'),
    path('parking-lots/<int:lot_id>/', views.owner_lot_detail_view, name='lot_detail'),
    path('parking-lots/<int:lot_id>/toggle-pause/', views.owner_toggle_pause_lot_view, name='toggle_pause_lot'),

    
    path('bookings/', views.owner_bookings_view, name='bookings'),
    path('bookings/<int:booking_id>/verify-entry/', views.owner_verify_entry_view, name='verify_entry'),
    path('bookings/<int:booking_id>/verify-exit/', views.owner_verify_exit_view, name='verify_exit'),

    path('extensions/', views.owner_extensions_view, name='extensions'),
    path('extensions/<int:ext_id>/approve/', views.owner_approve_extension_view, name='approve_extension'),
    path('extensions/<int:ext_id>/reject/', views.owner_reject_extension_view, name='reject_extension'),

    
    path('slots/', views.owner_slots_view, name='slots'),
    path('slots/<int:slot_id>/toggle-maintenance/', views.owner_toggle_slot_maintenance_view, name='toggle_slot_maintenance'),

    
    path('pricing/', views.owner_pricing_view, name='pricing'),

    
    path('ev-charging/', views.owner_ev_charging_view, name='ev_charging'),

    
    path('earnings/', views.owner_earnings_view, name='earnings'),
    path('earnings/statement/download/', views.owner_download_statement_view, name='download_statement'),

    
    path('reports/', views.owner_reports_view, name='reports'),

    
    path('reviews/', views.owner_reviews_view, name='reviews'),
    path('reviews/<int:review_id>/reply/', views.owner_reply_review_view, name='reply_review'),
    path('reviews/<int:review_id>/report/', views.owner_report_review_view, name='report_review'),

    
    path('notifications/', views.owner_notifications_view, name='notifications'),
    path('notifications/mark-all-read/', views.owner_mark_notifications_read_view, name='mark_notifications_read'),

    
    path('profile/', views.owner_profile_settings_view, name='profile_settings'),
    path('profile-settings/', views.owner_profile_settings_view, name='profile_settings_alt'),

    
    path('support/', views.owner_support_view, name='support'),
]

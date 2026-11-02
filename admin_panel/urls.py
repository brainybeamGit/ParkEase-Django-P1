from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Auth
    path('login/', views.admin_login_view, name='login'),
    path('logout/', views.admin_logout_view, name='logout'),

    # 1. Dashboard
    path('', views.admin_dashboard_view, name='dashboard'),
    path('dashboard/', views.admin_dashboard_view, name='dashboard_alt'),

    # 2. User Management
    path('users/', views.admin_users_view, name='users'),
    path('users/<int:user_id>/toggle-status/', views.admin_toggle_user_status_view, name='toggle_user_status'),
    path('users/<int:user_id>/delete/', views.admin_delete_user_view, name='delete_user'),

    # 3. Owner Verification
    path('owners/', views.admin_owner_verification_view, name='owner_verification'),
    path('owners/<int:owner_id>/approve/', views.admin_approve_owner_view, name='approve_owner'),
    path('owners/<int:owner_id>/reject/', views.admin_reject_owner_view, name='reject_owner'),

    # 4. Parking Lot Management
    path('parking-lots/', views.admin_parking_lots_view, name='parking_lots'),
    path('parking-lots/<int:lot_id>/approve/', views.admin_approve_lot_view, name='approve_lot'),
    path('parking-lots/<int:lot_id>/reject/', views.admin_reject_lot_view, name='reject_lot'),
    path('parking-lots/<int:lot_id>/toggle-status/', views.admin_toggle_lot_status_view, name='toggle_lot_status'),

    # 5. Booking Management
    path('bookings/', views.admin_bookings_view, name='bookings'),

    # 6. Payments & Refunds
    path('payments/', views.admin_payments_view, name='payments'),
    path('payments/<int:tx_id>/refund/', views.admin_process_refund_view, name='process_refund'),

    # 7. Commission & Payout Management
    path('payouts/', views.admin_payouts_view, name='payouts'),
    path('payouts/<int:payout_id>/mark-paid/', views.admin_mark_payout_paid_view, name='mark_payout_paid'),

    # 8. EV Charging Management
    path('ev-charging/', views.admin_ev_charging_view, name='ev_charging'),
    path('ev-charging/<int:charger_id>/toggle/', views.admin_toggle_charger_view, name='toggle_charger'),

    # 9. Pricing, Fines & Offers
    path('pricing/', views.admin_pricing_view, name='pricing'),
    path('pricing/coupon/create/', views.admin_create_coupon_view, name='create_coupon'),
    path('pricing/coupon/<int:coupon_id>/toggle/', views.admin_toggle_coupon_view, name='toggle_coupon'),

    # 10. Reports & Analytics
    path('reports/', views.admin_reports_view, name='reports'),
    path('reports/export/', views.admin_export_reports_view, name='export_reports'),

    # 11. Reviews & Ratings
    path('reviews/', views.admin_reviews_view, name='reviews'),
    path('reviews/<int:review_id>/moderate/', views.admin_moderate_review_view, name='moderate_review'),

    # 12. Complaints & Disputes
    path('complaints/', views.admin_complaints_view, name='complaints'),
    path('feedbacks/', views.admin_feedbacks_view, name='feedbacks'),
    path('complaints/<int:complaint_id>/resolve/', views.admin_resolve_complaint_view, name='resolve_complaint'),

    # 13. Notifications & Announcements
    path('notifications/', views.admin_notifications_view, name='notifications'),
    path('notifications/broadcast/', views.admin_broadcast_announcement_view, name='broadcast_announcement'),
    path('notifications/mark-all-read/', views.admin_mark_notifications_read_view, name='mark_notifications_read'),
    path('notifications/<int:notif_id>/dismiss/', views.admin_dismiss_notification_view, name='dismiss_notification'),

    # 14. System Settings & Audit Logs
    path('settings/', views.admin_settings_view, name='settings'),
    path('audit-logs/', views.admin_audit_logs_view, name='audit_logs'),

    # 15. Help & Support
    path('support/', views.admin_support_view, name='support'),
]

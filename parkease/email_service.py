

import os
import sys
import logging
import traceback
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailNotificationService:

    EVENT_CONFIG = {
        
        'user_registration': {
            'role': 'driver',
            'badge': 'WELCOME TO PARKEASE',
            'subject': 'Welcome to ParkEase - Your Account is Ready!',
            'headline': 'Welcome to Smarter, Guaranteed Parking!',
            'cta_text': 'Find Parking Spaces',
            'cta_path': '/',
            'security_note': 'If you did not create this ParkEase account, please contact support immediately.',
        },
        'email_verification': {
            'role': 'driver',
            'badge': 'EMAIL VERIFICATION',
            'subject': 'Verify Your ParkEase Email Address',
            'headline': 'Confirm Your Email Address',
            'cta_text': 'Verify Email',
            'cta_path': '/accounts/login/',
            'security_note': 'This verification link is time-limited. Do not forward this email.',
        },
        'login_security_alert': {
            'role': 'driver',
            'badge': 'SECURITY ALERT',
            'subject': 'Security Alert: New Sign-In to Your ParkEase Account',
            'headline': 'New Sign-In Detected',
            'cta_text': 'Review Account Security',
            'cta_path': '/accounts/login/',
            'security_note': 'If this was not you, change your password immediately and notify security.',
        },
        'forgot_password_otp': {
            'role': 'driver',
            'badge': 'PASSWORD RESET OTP',
            'subject': 'Your 6-Digit Password Reset OTP - ParkEase',
            'headline': 'Password Reset Request',
            'cta_text': 'Reset Your Password',
            'cta_path': '/accounts/forgot-password/',
            'security_note': 'Your 6-digit OTP is valid for 10 minutes. ParkEase staff will never ask for your OTP.',
        },
        'password_reset_success': {
            'role': 'driver',
            'badge': 'SECURITY UPDATE',
            'subject': 'Your ParkEase Password Has Been Successfully Reset',
            'headline': 'Password Changed Successfully',
            'cta_text': 'Sign In to Account',
            'cta_path': '/accounts/login/',
            'security_note': 'If you did not initiate this change, contact 1800-PARKEASE immediately.',
        },
        'profile_email_update': {
            'role': 'driver',
            'badge': 'EMAIL CHANGE VERIFICATION',
            'subject': 'Verify Your New Email Address for ParkEase',
            'headline': 'Confirm Your Updated Email',
            'cta_text': 'Confirm Email Change',
            'cta_path': '/accounts/login/',
            'security_note': 'Your current email will remain active until this change is confirmed.',
        },
        'parking_saved_search': {
            'role': 'driver',
            'badge': 'AVAILABILITY ALERT',
            'subject': 'Spaces Available for Your Saved Search',
            'headline': 'New Parking Spots Near Your Destination',
            'cta_text': 'View Available Bays',
            'cta_path': '/',
        },
        'booking_confirmation': {
            'role': 'driver',
            'badge': 'BOOKING CONFIRMED',
            'subject': 'Booking Confirmed: Your ParkEase Parking Pass & QR Ticket',
            'headline': 'Your Parking Reservation is Confirmed!',
            'cta_text': 'View Booking & QR Ticket',
            'cta_path': '/accounts/vehicles/',
            'security_note': 'Display your digital pass or QR token at the automated barrier or gate attendant.',
        },
        'payment_receipt': {
            'role': 'driver',
            'badge': 'PAYMENT RECEIPT',
            'subject': 'Payment Receipt for ParkEase Reservation',
            'headline': 'Payment Successful - Thank You!',
            'cta_text': 'Download Tax Invoice',
            'cta_path': '/',
        },
        'booking_reminder': {
            'role': 'driver',
            'badge': 'UPCOMING RESERVATION',
            'subject': 'Reminder: Your ParkEase Parking Starts Soon',
            'headline': 'Your Scheduled Parking Begins Shortly',
            'cta_text': 'Get Directions & QR Pass',
            'cta_path': '/',
        },
        'booking_cancellation': {
            'role': 'driver',
            'badge': 'BOOKING CANCELLED',
            'subject': 'Booking Cancellation Confirmation - ParkEase',
            'headline': 'Your Booking Has Been Cancelled',
            'cta_text': 'Explore Other Locations',
            'cta_path': '/',
            'security_note': 'Refunds for eligible cancellations are credited according to platform policy.',
        },
        'refund_update': {
            'role': 'driver',
            'badge': 'REFUND STATUS',
            'subject': 'ParkEase Refund Status Update',
            'headline': 'Refund Processed to Original Payment Method',
            'cta_text': 'View Transaction History',
            'cta_path': '/',
        },
        'entry_exit_confirmation': {
            'role': 'driver',
            'badge': 'PARKING SESSION UPDATE',
            'subject': 'ParkEase Gate Check-In / Check-Out Notice',
            'headline': 'Parking Session Recorded',
            'cta_text': 'View Parking Activity',
            'cta_path': '/',
        },
        'overstay_fine_notice': {
            'role': 'driver',
            'badge': 'OVERSTAY NOTICE',
            'subject': 'Overstay Notice: Additional Fee Applied to Booking',
            'headline': 'Parking Overstay Notice',
            'cta_text': 'Review Booking Overstay',
            'cta_path': '/',
            'security_note': 'Please ensure timely vehicle departure to avoid towing or additional penalties.',
        },
        'ev_charging_reservation': {
            'role': 'driver',
            'badge': 'EV CHARGING CONFIRMED',
            'subject': 'EV Fast Charging Bay Reserved - ParkEase EV',
            'headline': 'Your EV Charging Bay is Guaranteed',
            'cta_text': 'View Charger Pass',
            'cta_path': '/',
        },
        'ev_charging_session': {
            'role': 'driver',
            'badge': 'EV SESSION COMPLETED',
            'subject': 'EV Charging Session Summary & Electricity Receipt',
            'headline': 'Charging Session Complete',
            'cta_text': 'View Energy Receipt',
            'cta_path': '/',
        },
        'review_submitted': {
            'role': 'driver',
            'badge': 'REVIEW RECEIVED',
            'subject': 'Thank You for Reviewing Your Parking Experience!',
            'headline': 'Your Review Has Been Published',
            'cta_text': 'View Your Review',
            'cta_path': '/',
        },
        'complaint_ticket': {
            'role': 'driver',
            'badge': 'SUPPORT TICKET',
            'subject': 'Support Ticket Received - ParkEase Customer Care',
            'headline': 'We Have Received Your Support Request',
            'cta_text': 'Track Support Ticket',
            'cta_path': '/faqs-support/',
            'security_note': 'Our support team operates 24/7. An agent will respond shortly.',
        },
        'notification_settings': {
            'role': 'driver',
            'badge': 'PREFERENCES UPDATED',
            'subject': 'ParkEase Email & Notification Preferences Updated',
            'headline': 'Notification Settings Saved',
            'cta_text': 'Manage Account',
            'cta_path': '/accounts/vehicles/',
        },
                'feedback_submitted': {
            'role': 'driver',
            'badge': 'FEEDBACK RECEIVED',
            'subject': 'Thank You for Your Feedback! - ParkEase',
            'headline': 'Thank You for Your Feedback! Hope You Liked Our Service.',
            'cta_text': 'Find Parking Spaces',
            'cta_path': '/',
        },
        'admin_new_feedback_alert': {
            'role': 'admin',
            'badge': 'DIRECT USER FEEDBACK',
            'subject': 'New Direct Motorist Feedback Received - Admin Alert',
            'headline': 'Direct Motorist Feedback Received for Admin Action',
            'cta_text': 'Open Feedbacks Desk',
            'cta_path': '/admin-panel/feedbacks/',
        },
        'owner_new_review_alert': {
            'role': 'owner',
            'badge': 'NEW DRIVER REVIEW',
            'subject': 'New Driver Rating & Review Received - Space Owner Studio',
            'headline': 'New Driver Review Received for Your Facility',
            'cta_text': 'View Reviews in Studio',
            'cta_path': '/lot-owner/reviews/',
        },
        'driver_extension_approved': {
            'role': 'driver',
            'badge': 'PARKING EXTENSION APPROVED',
            'subject': 'Parking Time Extension Approved - ParkEase',
            'headline': 'Your Parking Duration Has Been Extended!',
            'cta_text': 'View Active Pass & Ticket',
            'cta_path': '/my-bookings/',
            'security_note': 'Please note that you must vacate the parking space promptly when your extended time expires.',
        },

    
        'owner_registration': {
            'role': 'owner',
            'badge': 'OWNER APPLICATION RECEIVED',
            'subject': 'Space Owner Application Received - ParkEase Partner Studio',
            'headline': 'Thank You for Applying to List Your Parking Space!',
            'cta_text': 'Open Space Owner Studio',
            'cta_path': '/lot-owner/dashboard/',
            'security_note': 'Our operations team reviews submissions within 24 business hours.',
        },
        'owner_email_verification': {
            'role': 'owner',
            'badge': 'OWNER VERIFICATION',
            'subject': 'Verify Your Space Owner Account Email - ParkEase',
            'headline': 'Verify Your Email to Activate Space Owner Studio',
            'cta_text': 'Verify Owner Account',
            'cta_path': '/lot-owner/login/',
        },
        'owner_verification_status': {
            'role': 'owner',
            'badge': 'KYC VERIFICATION UPDATE',
            'subject': 'Status Update: Your Owner Verification & KYC Documents',
            'headline': 'Verification Application Status Update',
            'cta_text': 'View Verification Status',
            'cta_path': '/lot-owner/dashboard/',
        },
        'parking_lot_registration': {
            'role': 'owner',
            'badge': 'PARKING FACILITY SUBMITTED',
            'subject': 'Parking Lot Submission Confirmation - ParkEase',
            'headline': 'New Parking Facility Submitted for Review',
            'cta_text': 'View My Parking Lots',
            'cta_path': '/lot-owner/parking-lots/',
        },
        'parking_lot_approval': {
            'role': 'owner',
            'badge': 'LOT APPROVAL STATUS',
            'subject': 'Your Parking Facility is Now LIVE on ParkEase!',
            'headline': 'Congratulations! Your Parking Lot is Approved & Live',
            'cta_text': 'Manage Live Bays',
            'cta_path': '/lot-owner/parking-lots/',
        },
        'owner_new_booking': {
            'role': 'owner',
            'badge': 'NEW DRIVER BOOKING',
            'subject': 'New Booking Alert: Vehicle Reserved at Your Facility',
            'headline': 'New Driver Reservation Received',
            'cta_text': 'View Booking Details',
            'cta_path': '/lot-owner/bookings/',
        },
        'owner_booking_cancelled': {
            'role': 'owner',
            'badge': 'BOOKING CANCELLED',
            'subject': 'Driver Booking Cancellation Alert - ParkEase',
            'headline': 'A Reservation Has Been Cancelled',
            'cta_text': 'View Bay Calendar',
            'cta_path': '/lot-owner/bookings/',
        },
        'owner_upcoming_summary': {
            'role': 'owner',
            'badge': 'DAILY ARRIVALS SCHEDULE',
            'subject': 'Daily Arrivals Summary for Your Parking Facility',
            'headline': 'Upcoming Reservations for Today',
            'cta_text': 'Open Bookings Dashboard',
            'cta_path': '/lot-owner/bookings/',
        },
        'owner_entry_exit': {
            'role': 'owner',
            'badge': 'GATE EVENT',
            'subject': 'Vehicle Check-In / Check-Out Recorded at Your Facility',
            'headline': 'Gate Entry / Exit Logged',
            'cta_text': 'View Live Occupancy',
            'cta_path': '/lot-owner/bookings/',
        },
        'owner_pricing_change': {
            'role': 'owner',
            'badge': 'PRICING UPDATED',
            'subject': 'Confirmation: Parking Tariff Rates Updated',
            'headline': 'Facility Pricing Successfully Updated',
            'cta_text': 'Review Pricing & Offers',
            'cta_path': '/lot-owner/pricing/',
        },
        'owner_ev_charger_registration': {
            'role': 'owner',
            'badge': 'EV CHARGER SUBMITTED',
            'subject': 'EV Charger Registered - Pending Technical Review',
            'headline': 'EV Charging Station Submission Received',
            'cta_text': 'Manage EV Station',
            'cta_path': '/lot-owner/ev-charging/',
        },
        'owner_ev_charging_fault': {
            'role': 'owner',
            'badge': 'CHARGER FAULT ALERT',
            'subject': 'URGENT: EV Charger Fault Reported at Your Facility',
            'headline': 'Technical Fault Reported on EV Charger',
            'cta_text': 'Investigate Charger Status',
            'cta_path': '/lot-owner/ev-charging/',
            'security_note': 'Ensure station safety. Offline bays are temporarily hidden from search.',
        },
        'owner_ev_reservation': {
            'role': 'owner',
            'badge': 'EV CHARGING RESERVATION',
            'subject': 'New EV Fast Charging Session Reserved at Your Facility',
            'headline': 'New EV Charging Booking Received',
            'cta_text': 'View EV Reservations',
            'cta_path': '/lot-owner/ev-charging/',
        },
        'owner_payout_status': {
            'role': 'owner',
            'badge': 'FINANCIAL SETTLEMENT',
            'subject': 'Bank Payout Dispatched - ParkEase Weekly Remittance',
            'headline': 'Your Bank Settlement Has Been Dispatched',
            'cta_text': 'View Earnings & Payouts',
            'cta_path': '/lot-owner/earnings/',
        },
        'owner_performance_report': {
            'role': 'owner',
            'badge': 'ANALYTICS REPORT',
            'subject': 'Your Weekly Parking Revenue & Performance Summary',
            'headline': 'Weekly Performance Analytics',
            'cta_text': 'View Detailed Reports',
            'cta_path': '/lot-owner/reports/',
        },
        'owner_review_alert': {
            'role': 'owner',
            'badge': 'NEW CUSTOMER REVIEW',
            'subject': 'New Motorist Review on Your Parking Facility',
            'headline': 'A Motorist Left a Review on Your Bay',
            'cta_text': 'Read Customer Reviews',
            'cta_path': '/lot-owner/reviews/',
        },
        'owner_dispute_assigned': {
            'role': 'owner',
            'badge': 'DISPUTE NOTIFICATION',
            'subject': 'Customer Inquiry / Dispute Assigned for Review',
            'headline': 'Inquiry Assigned Concerning Your Facility',
            'cta_text': 'Respond in Studio',
            'cta_path': '/lot-owner/dashboard/',
        },
        'owner_security_alert': {
            'role': 'owner',
            'badge': 'OWNER SECURITY ALERT',
            'subject': 'Security Notice: Bank Details or Profile Updated',
            'headline': 'Important Changes to Your Owner Account',
            'cta_text': 'Review Security Settings',
            'cta_path': '/lot-owner/profile/',
            'security_note': 'If you did not make this change, please freeze payouts and contact security.',
        },
        'owner_extension_request': {
            'role': 'owner',
            'badge': 'TIME EXTENSION REQUEST',
            'subject': 'Driver Extension Request: Action Required in Owner Studio',
            'headline': 'Motorist Requested Parking Time Extension',
            'cta_text': 'Review & Approve Extension',
            'cta_path': '/lot-owner/extensions/',
            'security_note': 'Check slot availability and subsequent motorist reservations before approving.',
        },

        
        'admin_security_alert': {
            'role': 'admin',
            'badge': 'ADMIN SECURITY NOTICE',
            'subject': 'Administrative Access Notification - ParkEase Admin Studio',
            'headline': 'Privileged Admin Login Detected',
            'cta_text': 'Open Admin Studio',
            'cta_path': '/admin-panel/',
        },
        'admin_pending_owner_review': {
            'role': 'admin',
            'badge': 'PENDING APPLICATION',
            'subject': 'Action Required: New Owner KYC Application Awaiting Review',
            'headline': 'New Space Owner Application Submitted',
            'cta_text': 'Review Owner Application',
            'cta_path': '/admin-panel/owners/verification/',
        },
        'admin_parking_lot_submission': {
            'role': 'admin',
            'badge': 'FACILITY APPROVAL',
            'subject': 'New Parking Facility Submitted for Admin Approval',
            'headline': 'Parking Lot Submission Awaiting Approval',
            'cta_text': 'Review Facility',
            'cta_path': '/admin-panel/parking-lots/',
        },
        'admin_user_status_notice': {
            'role': 'admin',
            'badge': 'USER ACCOUNT STATUS',
            'subject': 'Account Status Update - ParkEase Compliance Team',
            'headline': 'Your Account Status Has Been Updated',
            'cta_text': 'Contact Compliance',
            'cta_path': '/help-center/',
        },
        'admin_booking_exception': {
            'role': 'admin',
            'badge': 'SYSTEM EXCEPTION',
            'subject': 'Exception Alert: Unusual Booking Conflict or Overstay',
            'headline': 'Booking Exception Detected',
            'cta_text': 'Open Booking Manager',
            'cta_path': '/admin-panel/bookings/',
        },
        'admin_payment_reconciliation': {
            'role': 'admin',
            'badge': 'FINANCIAL ALERT',
            'subject': 'Payment Gateway Reconciliation / Refund Failure Alert',
            'headline': 'Payment Discrepancy or Refund Failure',
            'cta_text': 'Review Payments & Refunds',
            'cta_path': '/admin-panel/payments/',
        },
        'admin_payout_exception': {
            'role': 'admin',
            'badge': 'SETTLEMENT EXCEPTION',
            'subject': 'Owner Settlement Failure Alert - Banking Exception',
            'headline': 'Bank Payout Settlement Exception',
            'cta_text': 'Review Settlements',
            'cta_path': '/admin-panel/commissions/',
        },
        'admin_critical_ev_fault': {
            'role': 'admin',
            'badge': 'CRITICAL EV OUTAGE',
            'subject': 'CRITICAL: Multiple EV Chargers Offline or Station Fault',
            'headline': 'Critical EV Charger Fault Alert',
            'cta_text': 'EV Station Manager',
            'cta_path': '/admin-panel/ev-charging/',
        },
        'admin_pricing_policy_update': {
            'role': 'admin',
            'badge': 'POLICY UPDATE',
            'subject': 'Notice: Important Updates to ParkEase Platform Policies',
            'headline': 'Platform Policies & Terms Update',
            'cta_text': 'Read Updated Policy',
            'cta_path': '/about-us/',
        },
        'admin_high_priority_complaint': {
            'role': 'admin',
            'badge': 'HIGH PRIORITY DISPUTE',
            'subject': 'Escalation Alert: High Priority Dispute Approaching SLA Deadline',
            'headline': 'High-Priority Customer Complaint Escalated',
            'cta_text': 'Handle Case in Studio',
            'cta_path': '/admin-panel/complaints/',
        },
        'admin_flagged_review_alert': {
            'role': 'admin',
            'badge': 'CONTENT MODERATION',
            'subject': 'Moderator Alert: Review Flagged for Inappropriate Content',
            'headline': 'Reported Review Awaiting Moderation',
            'cta_text': 'Review Ratings Desk',
            'cta_path': '/admin-panel/reviews/',
        },
        'admin_scheduled_report': {
            'role': 'admin',
            'badge': 'PLATFORM ANALYTICS',
            'subject': 'Scheduled Platform Executive Summary & Turnover Report',
            'headline': 'Weekly Executive Metrics Report',
            'cta_text': 'View Admin Analytics',
            'cta_path': '/admin-panel/reports/',
        },
        'admin_announcement_broadcast': {
            'role': 'admin',
            'badge': 'OFFICIAL ANNOUNCEMENT',
            'subject': 'Important Platform Announcement from ParkEase',
            'headline': 'Official Platform Announcement',
            'cta_text': 'Open ParkEase',
            'cta_path': '/',
        },
        'admin_system_monitoring_alert': {
            'role': 'admin',
            'badge': 'SYSTEM HEALTH ALERT',
            'subject': 'System Monitoring Alert: Webhook, Delivery, or Server Notice',
            'headline': 'Infrastructure Monitoring Event',
            'cta_text': 'View System Health',
            'cta_path': '/admin-panel/settings/',
        },
        'admin_activity_log_record': {
            'role': 'admin',
            'badge': 'AUDIT LOG RECORD',
            'subject': 'Audit Log: Administrative Email Dispatch Recorded',
            'headline': 'Administrative Action Audit',
            'cta_text': 'Open Audit Trail',
            'cta_path': '/admin-panel/logs/',
        },

        
        'contact_us_inquiry': {
            'role': 'driver',
            'badge': 'INQUIRY ACKNOWLEDGEMENT',
            'subject': 'We Have Received Your Message - ParkEase Team',
            'headline': 'Thank You for Contacting ParkEase',
            'cta_text': 'Browse Help Topics',
            'cta_path': '/help-center/',
        },
        'owner_login_alert': {
            'role': 'owner',
            'badge': 'SECURITY ALERT',
            'subject': 'Security Alert: Sign-In to Your Space Owner Studio',
            'headline': 'New Sign-In Detected in Space Owner Studio',
            'cta_text': 'Open Studio Dashboard',
            'cta_path': '/lot-owner/dashboard/',
            'security_note': 'If you did not initiate this sign-in, change your password immediately.',
        },
        'vehicle_added': {
            'role': 'driver',
            'badge': 'VEHICLE REGISTERED',
            'subject': 'New Vehicle Added to Your ParkEase Account',
            'headline': 'Your Vehicle Has Been Successfully Registered',
            'cta_text': 'View Registered Vehicles',
            'cta_path': '/accounts/profile/',
        },
        'profile_updated': {
            'role': 'driver',
            'badge': 'PROFILE UPDATE',
            'subject': 'Your ParkEase Profile Details Have Been Updated',
            'headline': 'Account Profile Information Updated',
            'cta_text': 'Review Profile',
            'cta_path': '/accounts/profile/',
        },
        'owner_slots_added': {
            'role': 'owner',
            'badge': 'SLOTS ADDED',
            'subject': 'New Parking Bays Added to Your Facility',
            'headline': 'Parking Slots Successfully Configured',
            'cta_text': 'Manage Facility Slots',
            'cta_path': '/lot-owner/slots/',
        },
        'admin_price_change_alert': {
            'role': 'admin',
            'badge': 'TARIFF UPDATE',
            'subject': 'Tariff Update Notice: Facility Pricing Modified by Owner',
            'headline': 'Parking Lot Tariff Changed by Space Owner',
            'cta_text': 'Review Facility Pricing',
            'cta_path': '/admin-panel/pricing/',
        },
        'refund_approved_user': {
            'role': 'driver',
            'badge': 'REFUND APPROVED',
            'subject': 'Refund Approved: Payment Credited to Your Account',
            'headline': 'Your Refund Has Been Approved & Processed',
            'cta_text': 'View Booking Details',
            'cta_path': '/my-bookings/',
        },
        'refund_approved_admin': {
            'role': 'admin',
            'badge': 'REFUND PROCESSED',
            'subject': 'Refund Notification: Payment Reversal Confirmed',
            'headline': 'Booking Refund Successfully Processed',
            'cta_text': 'Open Payments Desk',
            'cta_path': '/admin-panel/payments/',
        },
        'admin_ev_maintenance_alert': {
            'role': 'admin',
            'badge': 'EV MAINTENANCE',
            'subject': 'EV Station Alert: Charger Set to Maintenance by Space Owner',
            'headline': 'EV Charger Placed in Maintenance Mode',
            'cta_text': 'Open EV Station Desk',
            'cta_path': '/admin-panel/ev-charging/',
        },
        'owner_review_response': {
            'role': 'driver',
            'badge': 'REVIEW RESPONSE',
            'subject': 'Response Received: Parking Lot Owner Replied to Your Review',
            'headline': 'The Parking Lot Owner Has Responded to Your Review',
            'cta_text': 'View Review on ParkEase',
            'cta_path': '/',
        },
        'owner_notification_alert': {
            'role': 'owner',
            'badge': 'NEW NOTIFICATION',
            'subject': 'New Alert in Space Owner Studio',
            'headline': 'You Have a New Notification',
            'cta_text': 'View Notifications',
            'cta_path': '/lot-owner/notifications/',
        },
        'owner_bank_updated': {
            'role': 'owner',
            'badge': 'SECURITY UPDATE',
            'subject': 'Security Alert: Space Owner Profile / Bank Details Updated',
            'headline': 'Your Personal & Banking Details Have Been Updated',
            'cta_text': 'Review Profile Settings',
            'cta_path': '/lot-owner/profile/',
        },
        'admin_owner_bank_alert': {
            'role': 'admin',
            'badge': 'BANK DETAILS UPDATE',
            'subject': 'Compliance Notice: Space Owner Bank Details Updated',
            'headline': 'Space Owner Updated Banking & Payout Credentials',
            'cta_text': 'Review Owner Profile',
            'cta_path': '/admin-panel/owners/',
        },
        'user_account_deleted': {
            'role': 'driver',
            'badge': 'ACCOUNT CLOSED',
            'subject': 'Important Notice: Your ParkEase Account Has Been Closed',
            'headline': 'Your ParkEase Account Has Been Removed',
            'cta_text': 'Contact Support',
            'cta_path': '/help-center/',
        },
        'owner_verification_approved': {
            'role': 'owner',
            'badge': 'KYC APPROVED',
            'subject': 'Congratulations! Your Space Owner Verification is Approved',
            'headline': 'Your Space Owner Account is Verified & Active',
            'cta_text': 'Open Space Owner Studio',
            'cta_path': '/lot-owner/dashboard/',
        },
        'owner_lot_paused': {
            'role': 'owner',
            'badge': 'FACILITY STATUS',
            'subject': 'Notice: Your Parking Facility Has Been Paused',
            'headline': 'Parking Facility Paused by Administration',
            'cta_text': 'Manage Parking Lots',
            'cta_path': '/lot-owner/parking-lots/',
        },
        'owner_ev_admin_maintenance': {
            'role': 'owner',
            'badge': 'CHARGER NOTICE',
            'subject': 'Operational Notice: EV Charger Placed Under Maintenance by Admin',
            'headline': 'EV Charger Marked for Maintenance by Platform Admin',
            'cta_text': 'View EV Charging Bays',
            'cta_path': '/lot-owner/ev-charging/',
        },
        'admin_notification_alert': {
            'role': 'admin',
            'badge': 'ADMIN ALERT',
            'subject': 'New Administrative Alert: Action Required',
            'headline': 'New Notification in Admin Studio',
            'cta_text': 'Open Admin Studio',
            'cta_path': '/admin-panel/notifications/',
        },
    }

    @classmethod
    def send_notification(
        cls,
        event_type,
        recipient_email,
        recipient_name=None,
        context=None,
        recipient_role=None,
        fail_silently=True
    ):
        
        from accounts.models import EmailDeliveryLog

        if not recipient_email:
            logger.warning("EmailNotificationService: Aborted sending, recipient_email is empty.")
            return False, "Recipient email is empty."

        config = cls.EVENT_CONFIG.get(event_type, {})
        ctx = context.copy() if context else {}

    
        subject = ctx.get('custom_subject') or config.get('subject', f'ParkEase Notification: {event_type.replace("_", " ").title()}')
        badge_text = ctx.get('badge_text') or config.get('badge', 'PARKEASE NOTIFICATION')
        headline = ctx.get('headline') or config.get('headline', subject)
        role = recipient_role or config.get('role', 'driver')

        
        site_url = ctx.get('site_url') or os.getenv('SITE_URL', 'http://127.0.0.1:8000')

        
        cta_text = ctx.get('cta_text') or config.get('cta_text')
        cta_url = ctx.get('cta_url')
        if not cta_url and config.get('cta_path'):
            cta_url = f"{site_url.rstrip('/')}{config['cta_path']}"

        
        template_context = {
            'subject': subject,
            'badge_text': badge_text,
            'headline': headline,
            'recipient_name': recipient_name or ctx.get('recipient_name', 'Valued Customer'),
            'message_body': ctx.get('message_body', 'This is an official automated notification regarding your ParkEase account.'),
            'otp_code': ctx.get('otp_code'),
            'details_dict': ctx.get('details_dict', {}),
            'cta_text': cta_text,
            'cta_url': cta_url,
            'security_note': ctx.get('security_note') or config.get('security_note'),
            'site_url': site_url,
        }

        
        try:
            html_content = render_to_string('emails/notification.html', template_context)
            text_content = strip_tags(html_content)
        except Exception as e:
            logger.error(f"Template rendering failed for email {event_type}: {e}")
            html_content = f"<p>{template_context['message_body']}</p>"
            text_content = template_context['message_body']

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'ParkEase <noreply@parkease.com>')
        smtp_user = getattr(settings, 'EMAIL_HOST_USER', '')
        smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')

        
        has_real_smtp = bool(
            smtp_user and 
            smtp_password and 
            not smtp_user.startswith('your_') and 
            not smtp_password.startswith('your_')
        )

        delivery_status = 'sent'
        error_msg = ''
        msg_id = f"pe_msg_{timezone.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"

        if has_real_smtp:
            
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[recipient_email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
                logger.info(f"[EMAIL DELIVERED] '{subject}' successfully sent to {recipient_email}")
            except Exception as e:
                delivery_status = 'failed'
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"[EMAIL SEND ERROR] Failed to send '{subject}' to {recipient_email}: {error_msg}")
                if not fail_silently:
                    raise e
        else:
            
            delivery_status = 'simulated'
            logger.info(
                f"[DEV SIMULATED EMAIL]\n"
                f"  Event: {event_type}\n"
                f"  To: {recipient_email} ({recipient_name})\n"
                f"  Subject: {subject}\n"
                f"  OTP Code: {ctx.get('otp_code', 'N/A')}\n"
                f"  Status: Recorded in EmailDeliveryLog (Configure .env for live SMTP delivery)"
            )

        
        try:
            EmailDeliveryLog.objects.create(
                recipient=recipient_email,
                recipient_name=recipient_name or '',
                recipient_role=role,
                event_type=event_type,
                subject=subject,
                status=delivery_status,
                error_message=error_msg,
                message_id=msg_id,
            )
        except Exception as log_err:
            logger.warning(f"Could not write EmailDeliveryLog: {log_err}")

        is_success = (delivery_status in ('sent', 'simulated'))
        return is_success, delivery_status

    

    @classmethod
    def send_user_welcome(cls, user):
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'message_body': (
                f"Welcome to ParkEase! Your driver account has been created successfully under <strong>{user.email}</strong>.<br><br>"
                "You can now search, reserve guaranteed parking spots ahead of time, access contactless bays, "
                "and manage your vehicle registrations from one unified portal."
            ),
            'details_dict': {
                'Username': user.username,
                'Registered Email': user.email,
                'Account Type': 'Motorist / Driver',
                'Registration Date': timezone.now().strftime('%B %d, %Y'),
            }
        }
        return cls.send_notification('user_registration', user.email, full_name, context, 'driver')

    @classmethod
    def send_forgot_password_otp(cls, user, otp_code):
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'otp_code': str(otp_code),
            'message_body': (
                "We received a request to reset the password for your ParkEase account. "
                "Please enter the 6-digit One-Time Password (OTP) displayed below to complete your password reset."
            ),
            'details_dict': {
                'Account Email': user.email,
                'Requested At': timezone.now().strftime('%H:%M:%S UTC, %B %d, %Y'),
                'Validity Period': '10 Minutes',
            }
        }
        return cls.send_notification('forgot_password_otp', user.email, full_name, context, 'driver')

    @classmethod
    def send_password_reset_success(cls, user):
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'message_body': (
                "The password for your ParkEase account was successfully changed. "
                "You can now use your new password to sign in across all ParkEase mobile and web applications."
            ),
            'details_dict': {
                'Account': user.email,
                'Updated At': timezone.now().strftime('%H:%M:%S UTC, %B %d, %Y'),
            }
        }
        return cls.send_notification('password_reset_success', user.email, full_name, context, 'driver')

    @classmethod
    def send_booking_confirmation(cls, booking):
        
        user = booking.user
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        reg_num = booking.vehicle.registration_number if booking.vehicle else 'Registered Plate'
        context = {
            'message_body': (
                f"Your parking reservation <strong>#{booking.id}</strong> has been confirmed at <strong>{booking.parking_lot}</strong>. "
                "Your space is guaranteed. Present your digital QR pass at the entrance gate for automated barrier opening."
            ),
            'details_dict': {
                'Booking Reference': f"#BK-{booking.id:04d}",
                'Parking Facility': booking.parking_lot,
                'Vehicle Plate': reg_num,
                'Arrival Date & Time': booking.start_time.strftime('%b %d, %Y %I:%M %p') if booking.start_time else 'Today',
                'Total Amount Paid': f"₹{booking.total_amount:.2f}",
                'QR Digital Pass Token': booking.qr_code_token or 'AUTOGENERATED-PASS',
            }
        }
        return cls.send_notification('booking_confirmation', user.email, full_name, context, 'driver')

    @classmethod
    def send_booking_cancellation(cls, booking):
        
        user = booking.user
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'message_body': (
                f"Your reservation <strong>#{booking.id}</strong> at <strong>{booking.parking_lot}</strong> has been cancelled. "
                "According to our cancellation policy, eligible refunds are credited to your original payment method within 5-7 working days."
            ),
            'details_dict': {
                'Booking ID': f"#BK-{booking.id:04d}",
                'Facility': booking.parking_lot,
                'Fee Settled': f"₹{booking.total_amount:.2f}",
                'Refund Status': 'Initiated to Original Payment Source',
            }
        }
        return cls.send_notification('booking_cancellation', user.email, full_name, context, 'driver')

    @classmethod
    def send_owner_registration_receipt(cls, owner_profile):

        user = owner_profile.user
        context = {
            'message_body': (
                f"Thank you for registering your property on ParkEase! Your application for <strong>{owner_profile.business_name}</strong> "
                "has been received by our partner operations desk. We will verify your submitted documents and approve your account shortly."
            ),
            'details_dict': {
                'Partner ID': f"OWN-{owner_profile.id:04d}",
                'Business / Property': owner_profile.business_name,
                'Contact Phone': owner_profile.phone,
                'Application Status': 'Under KYC & Document Review',
            }
        }
        return cls.send_notification('owner_registration', user.email, owner_profile.business_name, context, 'owner')

    @classmethod
    def send_owner_payout_notice(cls, payout):
        
        lot = payout.parking_lot
        owner_user = lot.owner
        context = {
            'message_body': (
                f"Good news! Your weekly parking remittance of <strong>₹{payout.net_amount:,.2f}</strong> has been dispatched "
                f"to your verified bank account for settlement period <strong>{payout.billing_cycle}</strong>."
            ),
            'details_dict': {
                'Bank Reference (UTR)': payout.payout_reference,
                'Gross Turnover': f"₹{payout.gross_amount:,.2f}",
                'Platform Commission': f"-₹{payout.platform_commission:,.2f}",
                'Net Dispatched Amount': f"₹{payout.net_amount:,.2f}",
                'Settlement Date': timezone.now().strftime('%B %d, %Y'),
            }
        }
        return cls.send_notification('owner_payout_status', owner_user.email, owner_user.first_name or owner_user.username, context, 'owner')

    @classmethod
    def send_admin_alert(cls, event_type, subject, message_body, details_dict=None):
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
        context = {
            'custom_subject': subject,
            'headline': subject,
            'message_body': message_body,
            'details_dict': details_dict or {},
        }
        return cls.send_notification(event_type, admin_email, 'Platform Admin', context, 'admin')

    @classmethod
    def send_user_login_alert(cls, user, ip='127.0.0.1'):
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'headline': 'New Sign-In to Your ParkEase Account',
            'message_body': (
                f"Hi {full_name},<br><br>"
                f"You have successfully signed in to your ParkEase Driver account on "
                f"<strong>{timezone.now().strftime('%B %d, %Y at %I:%M %p')}</strong>.<br>"
                "If this was you, you can safely disregard this email."
            ),
            'details_dict': {
                'Account Email': user.email,
                'Login Timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'Access IP': ip,
                'Platform Portal': 'Motorist / Customer Portal',
            }
        }
        return cls.send_notification('login_security_alert', user.email, full_name, context, 'driver')

    @classmethod
    def send_owner_login_alert(cls, user, ip='127.0.0.1'):
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'headline': 'New Sign-In to Your Space Owner Studio',
            'message_body': (
                f"Hi {full_name},<br><br>"
                f"You have successfully logged in to your ParkEase Space Owner Studio on "
                f"<strong>{timezone.now().strftime('%B %d, %Y at %I:%M %p')}</strong>.<br>"
                "If this was you, no action is needed."
            ),
            'details_dict': {
                'Space Owner Account': user.email,
                'Login Timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'Access IP': ip,
                'Portal': 'ParkEase Space Owner Studio',
            }
        }
        return cls.send_notification('owner_login_alert', user.email, full_name, context, 'owner')

    @classmethod
    def send_vehicle_added(cls, user, vehicle):
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'message_body': (
                f"Hi {full_name},<br><br>"
                f"Your vehicle <strong>{vehicle.registration_number}</strong> ({vehicle.make} {vehicle.model}) "
                "has been successfully registered to your ParkEase account. You can now use it for instant automated gate barrier clearance."
            ),
            'details_dict': {
                'Plate Number': vehicle.registration_number,
                'Vehicle Category': vehicle.get_vehicle_type_display(),
                'Make & Model': f"{vehicle.make} {vehicle.model}".strip() or 'N/A',
                'Electric Vehicle (EV)': 'Yes' if vehicle.is_ev else 'No',
                'Registration Date': timezone.now().strftime('%B %d, %Y'),
            }
        }
        return cls.send_notification('vehicle_added', user.email, full_name, context, 'driver')

    @classmethod
    def send_profile_updated(cls, user, mobile=''):
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        context = {
            'message_body': (
                f"Hi {full_name},<br><br>"
                "Your ParkEase profile and contact details were updated successfully on "
                f"<strong>{timezone.now().strftime('%B %d, %Y at %I:%M %p')}</strong>."
            ),
            'details_dict': {
                'Name': full_name,
                'Registered Email': user.email,
                'Contact Phone': mobile or 'Updated',
                'Updated At': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        }
        return cls.send_notification('profile_updated', user.email, full_name, context, 'driver')

    @classmethod
    def send_owner_slots_added(cls, owner_user, lot, count):
        
        full_name = f"{owner_user.first_name} {owner_user.last_name}".strip() or owner_user.username
        context = {
            'message_body': (
                f"Hi {full_name},<br><br>"
                f"Successfully added <strong>{count}</strong> new parking slot(s) to your facility <strong>{lot.name}</strong>. "
                "The bays are now indexed and available for motorists to discover and reserve."
            ),
            'details_dict': {
                'Facility': lot.name,
                'Location': f"{lot.area}, {lot.city}",
                'Bays Added': str(count),
                'Total Capacity': str(lot.total_slots),
                'Updated At': timezone.now().strftime('%B %d, %Y %I:%M %p'),
            }
        }
        return cls.send_notification('owner_slots_added', owner_user.email, full_name, context, 'owner')

    @classmethod
    def send_admin_price_change_alert(cls, lot, old_price, new_price, owner_user=None):
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
        owner_name = (f"{owner_user.first_name} {owner_user.last_name}".strip() if owner_user else None) or (lot.owner.username if lot.owner else 'Space Owner')
        context = {
            'message_body': (
                f"Space Owner <strong>{owner_name}</strong> has updated the tariff rates for parking facility <strong>{lot.name}</strong>.<br><br>"
                "Please review the revised rates in Admin Studio."
            ),
            'details_dict': {
                'Parking Facility': lot.name,
                'City / Area': f"{lot.area}, {lot.city}",
                'Space Owner': owner_name,
                'Standard Hourly Rate': f"₹{new_price} / hr",
                'Bike Hourly Rate': f"₹{lot.bike_rate or new_price} / hr",
                'SUV Hourly Rate': f"₹{lot.suv_rate or new_price} / hr",
                'Modified At': timezone.now().strftime('%B %d, %Y, %I:%M %p'),
            }
        }
        return cls.send_notification('admin_price_change_alert', admin_email, 'Platform Admin', context, 'admin')

    @classmethod
    def send_refund_approved(cls, booking):
        
        user = booking.user
        user_name = f"{user.first_name} {user.last_name}".strip() or user.username
        tx_id = booking.refund_transaction_id or getattr(booking, 'razorpay_payment_id', '') or f"RFND_{booking.id}"
        refund_amt = f"₹{booking.refund_amount if booking.refund_amount > 0 else booking.total_amount:.2f}"
        now_dt = booking.refund_processed_at or timezone.now()

        
        user_context = {
            'message_body': (
                f"Dear {user_name},<br><br>"
                f"Your refund request for booking <strong>#BK-{booking.id:04d}</strong> at <strong>{booking.parking_lot}</strong> "
                f"has been <strong>approved</strong>. The refund amount of <strong>{refund_amt}</strong> has been credited back "
                "to your original payment source via Razorpay."
            ),
            'details_dict': {
                'Motorist Name': user_name,
                'Refund Amount': refund_amt,
                'Transaction ID': tx_id,
                'Booking Reference': f"#BK-{booking.id:04d}",
                'Parking Facility': booking.parking_lot,
                'Approval Date & Time': now_dt.strftime('%B %d, %Y at %I:%M:%S %p'),
                'Settlement Mode': 'Original Payment Method (Razorpay Instant Reversal)',
            }
        }
        cls.send_notification('refund_approved_user', user.email, user_name, user_context, 'driver')

        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
        admin_context = {
            'message_body': (
                f"A gateway refund of <strong>{refund_amt}</strong> has been approved and dispatched for Booking <strong>#BK-{booking.id:04d}</strong>."
            ),
            'details_dict': {
                'User Account': f"{user_name} ({user.email})",
                'Refund Amount': refund_amt,
                'Refund Txn ID': tx_id,
                'Booking ID': f"#BK-{booking.id}",
                'Processed At': now_dt.strftime('%Y-%m-%d %H:%M:%S'),
            }
        }
        cls.send_notification('refund_approved_admin', admin_email, 'Platform Admin', admin_context, 'admin')

    @classmethod
    def send_ev_maintenance_alert(cls, charger, lot, set_by='owner'):
        
        charger_code = getattr(charger, 'charger_id', None) or getattr(charger, 'charger_code', None) or f"CHG-BAY-{charger.id}"
        power_rating = f"{charger.power_kw} kW" if hasattr(charger, 'power_kw') else 'Fast Charger'
        facility_name = lot.name

        if set_by == 'owner':
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
            context = {
                'message_body': (
                    f"Space Owner <strong>{lot.owner.username if lot.owner else 'Facility Operator'}</strong> has placed "
                    f"EV Charger <strong>{charger_code}</strong> at <strong>{facility_name}</strong> under maintenance."
                ),
                'details_dict': {
                    'Facility': facility_name,
                    'EV Charger Unit': charger_code,
                    'Charging Speed': power_rating,
                    'Connector Type': getattr(charger, 'connector_type', 'CCS2 / Type 2'),
                    'Status': 'Under Maintenance',
                    'Timestamp': timezone.now().strftime('%B %d, %Y %I:%M %p'),
                }
            }
            return cls.send_notification('admin_ev_maintenance_alert', admin_email, 'Platform Admin', context, 'admin')
        else:
            owner_user = lot.owner
            if not owner_user:
                return False, "No owner on lot"
            owner_name = f"{owner_user.first_name} {owner_user.last_name}".strip() or owner_user.username
            context = {
                'message_body': (
                    f"Hi {owner_name},<br><br>"
                    f"ParkEase Platform Administration has placed EV Charger <strong>{charger_code}</strong> at your facility "
                    f"<strong>{facility_name}</strong> under maintenance status."
                ),
                'details_dict': {
                    'Facility': facility_name,
                    'EV Charger Bay': charger_code,
                    'Maintenance Status': 'Scheduled Service / Offline',
                    'Updated By': 'Platform Administrator',
                    'Timestamp': timezone.now().strftime('%B %d, %Y %I:%M %p'),
                }
            }
            return cls.send_notification('owner_ev_admin_maintenance', owner_user.email, owner_name, context, 'owner')

    @classmethod
    def send_review_response(cls, review, response_text):
        
        user = review.user
        user_name = f"{user.first_name} {user.last_name}".strip() or user.username
        lot_name = review.parking_lot.name if hasattr(review, 'parking_lot') and review.parking_lot else (review.lot.name if hasattr(review, 'lot') else 'Parking Facility')
        context = {
            'message_body': (
                f"Hi {user_name},<br><br>"
                f"The verified space owner of <strong>{lot_name}</strong> has responded to your review:<br><br>"
                f"<blockquote style='border-left: 3px solid #0284c7; padding-left: 12px; margin: 12px 0; color: #475569; font-style: italic;'>"
                f"{response_text}"
                f"</blockquote>"
            ),
            'details_dict': {
                'Parking Facility': lot_name,
                'Your Rating': f"{review.rating} / 5 Stars",
                'Your Comment': review.comment or 'Review comment',
                'Owner Response Date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
            }
        }
        return cls.send_notification('owner_review_response', user.email, user_name, context, 'driver')

    @classmethod
    def send_owner_bank_updated(cls, owner_profile):
        
        user = owner_profile.user
        owner_name = f"{user.first_name} {user.last_name}".strip() or owner_profile.business_name or user.username
        masked_account = f"••••••{owner_profile.bank_account_number[-4:]}" if owner_profile.bank_account_number and len(owner_profile.bank_account_number) >= 4 else "Updated"
        now_str = timezone.now().strftime('%B %d, %Y at %I:%M %p')

        
        owner_context = {
            'message_body': (
                f"Hi {owner_name},<br><br>"
                "Security Notice: Your Space Owner profile and payout bank account details were updated successfully on "
                f"<strong>{now_str}</strong>.<br>"
                "If you did not authorize this change, please freeze your payouts and contact support immediately."
            ),
            'details_dict': {
                'Business Name': owner_profile.business_name,
                'Contact Phone': owner_profile.phone,
                'Bank Name': owner_profile.bank_name or 'Configured Bank',
                'Account Number': masked_account,
                'IFSC Code': owner_profile.bank_ifsc or 'Configured',
                'Updated At': now_str,
            }
        }
        cls.send_notification('owner_bank_updated', user.email, owner_name, owner_context, 'owner')

        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
        admin_context = {
            'message_body': (
                f"Space Owner <strong>{owner_name}</strong> ({owner_profile.business_name}) has updated their bank and payout details.<br>"
                "Please verify compliance before next automated disbursement."
            ),
            'details_dict': {
                'Owner User': f"{user.username} ({user.email})",
                'Business': owner_profile.business_name,
                'Bank Name': owner_profile.bank_name or 'Updated',
                'Account': masked_account,
                'IFSC': owner_profile.bank_ifsc,
                'Timestamp': now_str,
            }
        }
        cls.send_notification('admin_owner_bank_alert', admin_email, 'Platform Admin', admin_context, 'admin')

    @classmethod
    def send_user_deleted(cls, user_email, user_name):
        
        context = {
            'message_body': (
                f"Dear {user_name},<br><br>"
                "This email confirms that your ParkEase account has been closed and removed by platform administration.<br>"
                "If you have outstanding questions or believe this was an error, please contact our help desk."
            ),
            'details_dict': {
                'Registered Email': user_email,
                'Account Status': 'Deactivated / Closed',
                'Closure Timestamp': timezone.now().strftime('%B %d, %Y, %I:%M %p'),
            }
        }
        return cls.send_notification('user_account_deleted', user_email, user_name, context, 'driver')

    @classmethod
    def send_owner_verification_approved(cls, owner_profile):
       
        user = owner_profile.user
        owner_name = f"{user.first_name} {user.last_name}".strip() or owner_profile.business_name or user.username
        context = {
            'message_body': (
                f"Congratulations {owner_name}!<br><br>"
                f"Your KYC documentation and Space Owner account for <strong>{owner_profile.business_name}</strong> "
                "have been officially <strong>approved</strong> by ParkEase compliance.<br>"
                "You can now publish parking facilities, add bays, monitor real-time vehicle entries, and receive weekly payouts."
            ),
            'details_dict': {
                'Business Name': owner_profile.business_name,
                'Partner ID': f"OWN-{owner_profile.id:04d}",
                'Status': 'Verified & Approved',
                'Approval Date': timezone.now().strftime('%B %d, %Y'),
            }
        }
        return cls.send_notification('owner_verification_approved', user.email, owner_name, context, 'owner')

    @classmethod
    def send_owner_lot_paused(cls, lot):
        
        owner_user = lot.owner
        if not owner_user:
            return False, "No owner"
        owner_name = f"{owner_user.first_name} {owner_user.last_name}".strip() or owner_user.username
        context = {
            'message_body': (
                f"Hi {owner_name},<br><br>"
                f"Your parking facility <strong>{lot.name}</strong> located at <strong>{lot.area}, {lot.city}</strong> "
                "has been temporarily <strong>paused</strong> by platform administration. It is currently hidden from search discovery."
            ),
            'details_dict': {
                'Facility Name': lot.name,
                'Location': f"{lot.area}, {lot.city}",
                'Status': 'Paused / Hidden',
                'Effective Date': timezone.now().strftime('%B %d, %Y %I:%M %p'),
            }
        }
        return cls.send_notification('owner_lot_paused', owner_user.email, owner_name, context, 'owner')

    @classmethod
    def send_owner_notification_email(cls, owner_user, title, message):
        
        owner_name = f"{owner_user.first_name} {owner_user.last_name}".strip() or owner_user.username
        context = {
            'headline': title,
            'message_body': f"Hi {owner_name},<br><br>{message}",
            'details_dict': {
                'Notification Title': title,
                'Time': timezone.now().strftime('%B %d, %Y %I:%M %p'),
                'Portal': 'Space Owner Studio',
            }
        }
        return cls.send_notification('owner_notification_alert', owner_user.email, owner_name, context, 'owner')

    @classmethod
    def send_admin_notification_email(cls, title, message):
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
        context = {
            'headline': title,
            'message_body': f"New alert received in ParkEase Admin Studio:<br><br>{message}",
            'details_dict': {
                'Alert Title': title,
                'Time': timezone.now().strftime('%B %d, %Y %I:%M %p'),
                'Console': 'ParkEase Admin Studio',
            }
        }
        return cls.send_notification('admin_notification_alert', admin_email, 'Platform Admin', context, 'admin')

    @classmethod
    def send_owner_extension_request(cls, ext_req):
        
        booking = ext_req.booking
        owner_user = None
        if booking.lot and booking.lot.owner:
            owner_user = booking.lot.owner

        owner_email = owner_user.email if (owner_user and owner_user.email) else getattr(settings, 'LOT_OWNER_EMAIL', 'savaniiictiu62@gmail.com')
        owner_name = (f"{owner_user.first_name} {owner_user.last_name}".strip() or owner_user.username) if owner_user else "Space Owner"

        driver = ext_req.requested_by
        driver_name = f"{driver.first_name} {driver.last_name}".strip() or driver.username
        reg_num = booking.vehicle.registration_number if booking.vehicle else 'N/A'
        slot_name = booking.slot.slot_number if booking.slot else 'Assigned Space'

        conflict_note = "⚠️ OVERLAP ALERT: " + ext_req.conflict_details if ext_req.conflict_detected else "No conflicting bookings detected during requested extension period."

        context = {
            'subject': f"Time Extension Request: Booking #BK-{booking.id:04d} - {booking.parking_lot}",
            'headline': f"Parking Extension Request: Booking #BK-{booking.id:04d}",
            'message_body': (
                f"Hello {owner_name},<br><br>"
                f"Motorist <strong>{driver_name}</strong> has submitted a request to extend their active parking reservation at <strong>{booking.parking_lot}</strong>.<br>"
                f"Please review the schedule in Space Owner Studio and approve the request, or reassign an alternate available slot.<br><br>"
                f"<strong>Conflict Status:</strong> {conflict_note}"
            ),
            'details_dict': {
                'Booking Reference': f"#BK-{booking.id:04d}",
                'Motorist Name': driver_name,
                'Vehicle Plate': reg_num,
                'Parking Facility': booking.parking_lot,
                'Current Bay / Slot': slot_name,
                'Original Departure Time': ext_req.current_end_time.strftime('%b %d, %Y %I:%M %p'),
                'Requested Extra Duration': f"+{ext_req.additional_hours:.0f} hour(s)",
                'Requested New Departure': ext_req.requested_new_end_time.strftime('%b %d, %Y %I:%M %p'),
                'Additional Tariff Payable': f"₹{ext_req.additional_fee:.2f}",
                'Subsequent Booking Conflict': 'YES (Action Required)' if ext_req.conflict_detected else 'None (Slot Free)',
            }
        }
        return cls.send_notification('owner_extension_request', owner_email, owner_name, context, 'owner')

    @classmethod
    def send_driver_extension_approved(cls, ext_req):
        
        booking = ext_req.booking
        driver = ext_req.requested_by
        driver_email = driver.email or getattr(settings, 'USER_EMAIL', 'saavanbaems@gmail.com')
        driver_name = f"{driver.first_name} {driver.last_name}".strip() or driver.username

        slot_name = ext_req.assigned_slot.slot_number if ext_req.assigned_slot else (booking.slot.slot_number if booking.slot else 'Assigned Bay')
        lot_name = ext_req.assigned_lot.name if ext_req.assigned_lot else booking.parking_lot
        new_end_str = booking.end_time.strftime('%b %d, %Y %I:%M %p') if booking.end_time else ext_req.requested_new_end_time.strftime('%b %d, %Y %I:%M %p')

        context = {
            'subject': f"Parking Time Extension Approved: Booking #BK-{booking.id:04d} - {lot_name}",
            'headline': "Your Parking Duration Extension is Approved!",
            'message_body': (
                f"Hello {driver_name},<br><br>"
                f"Great news! The space owner has approved your parking extension request for booking <strong>#BK-{booking.id:04d}</strong> at <strong>{lot_name}</strong>.<br>"
                f"Your scheduled departure time has been successfully updated to <strong>{new_end_str}</strong>.<br><br>"
                f"<strong>IMPORTANT NOTICE:</strong> Please note that you have been granted extra parking time, but <strong>you must vacate the parking space promptly when this time is over ({new_end_str})</strong>, as subsequent bookings have been reserved and paid by other motorists.<br>"
                + (f"<br><strong>Owner Instructions:</strong> {ext_req.owner_note}" if ext_req.owner_note else "")
            ),
            'details_dict': {
                'Booking Reference': f"#BK-{booking.id:04d}",
                'Facility': lot_name,
                'Assigned Bay / Slot': slot_name,
                'Confirmed Departure Time': new_end_str,
                'Additional Time Added': f"+{ext_req.additional_hours:.0f} hour(s)",
                'Total Booking Tariff': f"₹{booking.total_amount:.2f}",
                'Status': 'Extension Approved & Active',
            }
        }
        return cls.send_notification('driver_extension_approved', driver_email, driver_name, context, 'driver')


    @classmethod
    def send_user_feedback_acknowledgment(cls, feedback):
        
        recipient_email = feedback.email or getattr(settings, 'USER_EMAIL', 'saavanbaems@gmail.com')
        recipient_name = feedback.name or 'Valued Motorist'
        cat_display = feedback.get_category_display() if hasattr(feedback, 'get_category_display') else feedback.category
        stars = "★" * feedback.rating + "☆" * (5 - feedback.rating)

        context = {
            'subject': 'Thank You for Your Feedback! - ParkEase',
            'headline': 'Thank You for Your Feedback! Hope You Liked Our Service.',
            'message_body': (
                f"Hello {recipient_name},<br><br>"
                "Thank you for sharing your feedback with the ParkEase administration team! <strong>Hope you liked our service.</strong><br><br>"
                "We truly appreciate you taking the time to share your experience and thoughts. Your feedback has been delivered directly to our platform leadership and operations desk to help us continually enhance your urban parking experience."
            ),
            'details_dict': {
                'Feedback Reference': f"#FB-{feedback.id:04d}",
                'Category': cat_display,
                'Experience Rating': f"{stars} ({feedback.rating} / 5 Stars)",
                'Your Message': feedback.message,
                'Sent To': 'ParkEase Platform Administration',
                'Status': 'Received & Under Admin Review',
            }
        }
        return cls.send_notification('feedback_submitted', recipient_email, recipient_name, context, 'driver')

    @classmethod
    def send_admin_new_feedback_alert(cls, feedback):
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
        cat_display = feedback.get_category_display() if hasattr(feedback, 'get_category_display') else feedback.category
        stars = "★" * feedback.rating + "☆" * (5 - feedback.rating)

        context = {
            'subject': f"New Direct Platform Feedback: {cat_display} ({feedback.rating}★)",
            'headline': "Direct Motorist Feedback Received for Admin Action",
            'message_body': (
                f"Hello Platform Admin,<br><br>"
                f"A motorist has submitted direct feedback via the ParkEase platform feedback card.<br>"
                f"<strong>Sender:</strong> {feedback.name} ({feedback.email})<br>"
                f"<strong>Rating:</strong> {stars} ({feedback.rating}/5)<br><br>"
                f"<strong>Feedback Message:</strong><br>"
                f"<blockquote style='border-left: 3px solid #0284c7; padding-left: 12px; margin: 12px 0; color: #475569; font-style: italic;'>"
                f"{feedback.message}"
                f"</blockquote>"
            ),
            'details_dict': {
                'Feedback ID': f"#FB-{feedback.id:04d}",
                'Complainant / Submitter': feedback.name,
                'Contact Email': feedback.email,
                'Category': cat_display,
                'Rating': f"{feedback.rating} / 5 Stars",
                'Date Received': timezone.now().strftime('%b %d, %Y %I:%M %p'),
            }
        }
        return cls.send_notification('admin_new_feedback_alert', admin_email, 'Platform Admin', context, 'admin')

    @classmethod
    def send_user_review_acknowledgment(cls, review):
        
        user = review.user
        recipient_email = user.email if (user and user.email) else getattr(settings, 'USER_EMAIL', 'saavanbaems@gmail.com')
        recipient_name = review.driver_name or (f"{user.first_name} {user.last_name}".strip() if user else 'Valued Motorist')
        lot = review.parking_lot
        lot_name = lot.name if lot else 'Parking Facility'
        owner = lot.owner if lot else None
        owner_name = f"{owner.first_name} {owner.last_name}".strip() or (owner.username if owner else 'Verified Space Owner')
        stars = "★" * review.rating + "☆" * (5 - review.rating)

        context = {
            'subject': f"Thank You for Rating Your Parking Experience at {lot_name} - ParkEase",
            'headline': "Thank You for Your Rating & Review! Hope You Liked Our Service.",
            'message_body': (
                f"Hello {recipient_name},<br><br>"
                f"Thank you for submitting your rating and review for <strong>{lot_name}</strong>! <strong>Hope you liked our service.</strong><br><br>"
                f"Your rating directly affects the total verified score of space owner <strong>{owner_name}</strong> and helps fellow drivers find high-quality, trusted parking bays across the ParkEase network."
            ),
            'details_dict': {
                'Parking Facility': lot_name,
                'Space Owner': owner_name,
                'Booking Reference': review.booking_ref,
                'Your Rating': f"{stars} ({review.rating} / 5 Stars)",
                'Your Feedback': review.comment,
                'Submission Date': timezone.now().strftime('%b %d, %Y %I:%M %p'),
                'Status': 'Published to Facility & Owner Profile',
            }
        }
        return cls.send_notification('review_submitted', recipient_email, recipient_name, context, 'driver')

    @classmethod
    def send_owner_new_review_alert(cls, review):
        
        lot = review.parking_lot
        owner = lot.owner if lot else None
        owner_email = owner.email if (owner and owner.email) else getattr(settings, 'LOT_OWNER_EMAIL', 'savaniiictiu62@gmail.com')
        owner_name = f"{owner.first_name} {owner.last_name}".strip() or (owner.username if owner else 'Space Owner')
        lot_name = lot.name if lot else 'Parking Lot'
        stars = "★" * review.rating + "☆" * (5 - review.rating)

        from django.db.models import Avg
        from lot_owner_panel.models import LotReview
        owner_avg = LotReview.objects.filter(parking_lot__owner=owner).aggregate(avg=Avg('rating'))['avg']
        owner_avg_str = f"{float(owner_avg):.1f}★" if owner_avg else "5.0★"

        context = {
            'subject': f"New Driver Rating: {review.rating}★ for {lot_name} - Space Owner Studio",
            'headline': f"New Driver Review Received for {lot_name}",
            'message_body': (
                f"Hello {owner_name},<br><br>"
                f"Driver <strong>{review.driver_name}</strong> has submitted a verified rating and review for your facility <strong>{lot_name}</strong>.<br>"
                f"This rating has been added to your facility profile and has updated your total space owner rating to <strong>{owner_avg_str}</strong>.<br><br>"
                f"<strong>Driver Feedback:</strong><br>"
                f"<blockquote style='border-left: 3px solid #10b981; padding-left: 12px; margin: 12px 0; color: #475569; font-style: italic;'>"
                f"{review.comment}"
                f"</blockquote><br>"
                f"You can view driver feedback and publish official owner replies directly from your Space Owner Studio."
            ),
            'details_dict': {
                'Parking Facility': lot_name,
                'Driver Plate / Name': review.driver_name,
                'Booking Reference': review.booking_ref,
                'Driver Rating': f"{stars} ({review.rating} / 5 Stars)",
                'Your New Total Owner Rating': owner_avg_str,
                'Date Received': timezone.now().strftime('%b %d, %Y %I:%M %p'),
            }
        }
        return cls.send_notification('owner_new_review_alert', owner_email, owner_name, context, 'owner')

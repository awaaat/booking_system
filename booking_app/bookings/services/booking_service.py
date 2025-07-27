import logging
from datetime import timedelta, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, models
from django.db.models import Q
from rest_framework.exceptions import ValidationError as RestValidationError # type: ignore
import secrets
from decimal import Decimal, ROUND_HALF_UP


from users.models.appuser import CustomUser
from listings.models.listing import Listing
from bookings.models.booking import Booking

logger = logging.getLogger("bookings")

class BookingService:
    """
    Manages booking-related business logic for a booking platform.
    Handles creation, confirmation, cancellation, and retrieval of bookings.
    Ensures only guests can create bookings, enforces availability, and manages email confirmations.
    All logic is confined to the service layer, leaving request/response handling to views.
    """
    
    @staticmethod
    def create_booking(user:CustomUser, data:dict) -> Booking:
        """
        Creates a booking for a guest user with PENDING status and sends a confirmation email.
        Validates listing availability, guest permissions, and prevents double-booking.
        Updates listing availability atomically.
        """
        if user.user_role != 'guest':
            raise PermissionDenied("Only guests can make a booking")
        if not user.is_email_verified:
            raise PermissionDenied("Only verified users can perform this action")
        listing_id = data.get('listing_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        guests = data.get('guests', 1)
        special_requests = data.get('special_requests')
        
        with transaction.atomic():
            try:
                listing = Listing.objects.select_for_update().get(property_id = listing_id)
                date_range = BookingService._generate_date_range(start_date, end_date) # type: ignore
                for date_str in date_range:
                    if not listing.availability.get(date_str, False):
                        raise RestValidationError(f"Property not available for booking for the given dates")
            except Listing.DoesNotExist:
                raise RestValidationError("Property does not exist")
            
            #validating dates
            # Validate dates
            if end_date <= start_date: # type: ignore
                raise RestValidationError("End date must be after start date")

            # Check for overlapping bookings
            overlapping = Booking.objects.filter(
                listing=listing,
                end_date__gt=start_date,
                start_date__lt=end_date,
                booking_status__in=['PENDING', 'CONFIRMED']
            )
            if overlapping.exists():
                raise RestValidationError("This listing is already booked for the selected dates")
                        # Validate guest count
            if guests > listing.capacity:
                raise RestValidationError(f"Number of guests ({guests}) exceeds listing capacity ({listing.capacity})")

            # Validate check-in/check-out time compatibility
            if listing.check_in_time and start_date.time() < listing.check_in_time: # type: ignore
                raise RestValidationError(f"Check-in time must be after {listing.check_in_time}")
            if listing.check_out_time and end_date.time() > listing.check_out_time: # type: ignore
                raise RestValidationError(f"Check-out time must be before {listing.check_out_time}")

            # Calculate pricing
            nights = len(date_range)
            base_price = Decimal(listing.price_per_night * nights).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            service_fee = (base_price * Decimal(str(settings.SERVICE_FEE_PERCENTAGE))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            tax_amount = (base_price * Decimal(str(settings.TAX_PERCENTAGE))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_amount = (base_price + service_fee + tax_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Determine cancellation deadline
            cancellation_days = {
                'flexible': 1,
                'moderate': 5,
                'strict': 7,
                'non_refundable': 0
            }.get(listing.cancellation_policy, 1)
            cancellation_deadline = start_date - timedelta(days=cancellation_days) if cancellation_days > 0 else None # type: ignore

            # Create booking
            booking = Booking(
                listing=listing,
                user=user,
                guests=guests,
                start_date=start_date,
                end_date=end_date,
                booking_status='PENDING' if not data.get('is_instant_book', False) else 'CONFIRMED',
                payment_status='PENDING',
                total_amount=total_amount,
                tax_amount=tax_amount,
                service_fee=service_fee,
                cancellation_deadline=cancellation_deadline,
                special_requests=special_requests,
                is_instant_book=data.get('is_instant_book', False),
                last_modified_by=user,
                activation_code=secrets.token_urlsafe(32) if not data.get('is_instant_book', False) else '',
                activation_code_expiry=timezone.now() + timedelta(minutes=30) if not data.get('is_instant_book', False) else None
            )

            booking.full_clean()
            booking.save()
            BookingService._update_listing_availability(listing, date_range, False)
            listing.save()
            
            BookingService._log_booking_action(booking, user, "CREATED")
            
            #send confirmation email
            if not booking.is_instant_book:
                BookingService._send_booking_confirmation_email(booking)
            BookingService._notify_host_new_booking(booking)
        return booking
    
    @staticmethod
    def _send_booking_confirmation_email(booking):
        """A method for sending booking confirmation email
        
        Args:
            booking (_type_): _description_
        """
        try:
            confirmation_url = f"{settings.SITE_URL}/booking/confirm/{booking.booking_id}/{booking.activation_code}"
            send_mail(
                subject="Confirm your Booking",
                message=(
                    f"Dear {booking.user.first_name}\n\n"
                    f"Please confirm your booking for {booking.listing.name}"
                    f"from {booking.start_date.strftime('%Y-%m-%d %H:%M')} to {booking.end_date.strftime('%Y-%m-%d %H:%M')} "
                    f"by clicking the following link: {confirmation_url}\n\n"
                    f"This link expires at {booking.activation_code_expiry.strftime('%Y-%m-%d %H:%M:%S %Z')}.\n"
                    
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[booking.user.email],
                fail_silently=False,
            )
            logger.info(f"Booking confirmation email sent to {booking.user.email} for booking {booking.booking_id}")
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email to {booking.user.email}: {str(e)}")
            raise
        
    
    @staticmethod
    def _notify_host_new_booking(booking: Booking):
        """
        Notifies the host of a new booking.
        """
        try:
            send_mail(
                subject="New Booking for Your Listing",
                message=(
                    f"Dear {booking.listing.host.first_name},\n\n"
                    f"A new booking has been made for your listing '{booking.listing.name}' "
                    f"by {booking.user.first_name} {booking.user.last_name} "
                    f"from {booking.start_date.strftime('%Y-%m-%d %H:%M')} to {booking.end_date.strftime('%Y-%m-%d %H:%M')}.\n"
                    f"Status: {booking.booking_status}\n"
                    f"Guests: {booking.guests}\n"
                    f"Special Requests: {booking.special_requests or 'None'}\n"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[booking.listing.host.email],
                fail_silently=False,
            )
            logger.info(f"Host notification email sent to {booking.listing.host.email} for booking {booking.booking_id}")
        except Exception as e:
            logger.error(f"Failed to send host notification email to {booking.listing.host.email}: {str(e)}")
            raise
            
    @staticmethod
    def confirm_booking(booking_id: str, code: str) -> Booking:
        """
        Confirms a booking if the provided activation code is valid and not expired.
        Updates listing availability and notifies the host.
        """
        with transaction.atomic():
            try:
                booking = Booking.objects.select_for_update().get(booking_id=booking_id)
                if booking.is_instant_book:
                    raise RestValidationError("Instant bookings do not require confirmation")
                if booking.activation_code_expiry and booking.activation_code_expiry < timezone.now():
                    raise RestValidationError("Booking confirmation code has expired")
                if booking.activation_code != code:
                    raise RestValidationError("Invalid booking confirmation code")
                if booking.booking_status != 'PENDING':
                    raise RestValidationError("Booking is not in a pending state")

                booking.booking_status = 'CONFIRMED'
                booking.activation_code = ''
                booking.activation_code_expiry = None
                booking.last_modified_by = booking.user
                booking.save()

                # Log action and notify host
                BookingService._log_booking_action(booking, booking.user, "CONFIRMED")
                BookingService._notify_host_booking_status_change(booking, "confirmed")

                logger.info(f"Booking {booking.booking_id} confirmed for user {booking.user.email}")
                return booking
            except Booking.DoesNotExist:
                logger.error(f"Booking with ID {booking_id} not found")
                raise RestValidationError("Booking not found")
            except Exception as e:
                logger.error(f"Booking confirmation failed: {str(e)}")
                raise
    @staticmethod
    def cancel_booking(user: CustomUser, booking: Booking):
        """
        Cancels a booking if the user is the guest or an admin and the cancellation deadline has not passed.
        Updates listing availability and processes refunds.
        """
        with transaction.atomic():
            if not (user.is_staff or (user.user_role == 'guest' and booking.user == user)):
                raise PermissionDenied("Only the guest or admin can cancel this booking")

            if booking.booking_status not in ['PENDING', 'CONFIRMED']:
                raise RestValidationError("Booking cannot be cancelled in its current state")

            if booking.cancellation_deadline and timezone.now() > booking.cancellation_deadline:
                raise RestValidationError("Cancellation deadline has passed")

            # Process refund
            refund_amount = BookingService._calculate_refunded_amount(booking)
            if refund_amount > 0:
                booking.payment_status = 'FULLY_REFUNDED' if refund_amount == booking.total_amount else 'PARTIALLY_REFUNDED'

            booking.booking_status = 'CANCELLED'
            booking.last_modified_by = user

            # Restore listing availability
            date_range = BookingService._generate_date_range(booking.start_date, booking.end_date)
            BookingService._update_listing_availability(booking.listing, date_range, True)
            booking.listing.save()

            booking.save()

            # Log action and notify
            BookingService._log_booking_action(booking, user, f"CANCELLED (Refund: {refund_amount})")
            BookingService._notify_guest_booking_status_change(booking, "cancelled", refund_amount)
            BookingService._notify_host_booking_status_change(booking, "cancelled")

            logger.info(f"Booking {booking.booking_id} cancelled by {user.email}")
    @staticmethod
    def get_bookings_for_user(user: CustomUser, listing: Listing, status: Optional[str] = None) -> 'models.QuerySet[Booking]':
        """
        Retrieves bookings linked to a specific listing, respecting user roles.
        """
        if not user.is_authenticated:
            raise PermissionDenied("You must be authenticated to view bookings")

        if not listing:
            raise RestValidationError("Listing instance is required")

        queryset = Booking.objects.filter(listing=listing)

        if user.is_staff:
            pass  # Admins see all bookings for the listing
        elif user.user_role == 'host':
            if listing.host != user:
                raise PermissionDenied("Hosts can only see bookings for their own listings")
        elif user.user_role == 'guest':
            queryset = queryset.filter(user=user)
        else:
            raise PermissionDenied("Invalid user role")

        if status:
            valid_statuses = [choice[0] for choice in Booking.booking_status.field.choices]  # type: ignore
            if status not in valid_statuses:
                raise RestValidationError(f"Invalid booking status: {status}")
            queryset = queryset.filter(booking_status=status)

        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_booking_by_id(booking_id: str) -> Booking:
        """
        Retrieves a single booking by its ID.
        """
        try:
            return Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            raise RestValidationError("Booking does not exist")
        except Exception as e:
            raise RestValidationError(f"Error: Invalid booking ID - {str(e)}")

    @staticmethod
    def update_payment_status(booking: Booking, payment_status: str, user: CustomUser, amount: Optional[Decimal] = None) -> Booking:
        """
        Updates the payment status of a booking (admin-only).
        """
        with transaction.atomic():
            if not user.is_staff:
                raise PermissionDenied("Only admins can update payment status")

            valid_statuses = [choice[0] for choice in Booking.payment_status.field.choices] # type: ignore
            if payment_status not in valid_statuses:
                raise RestValidationError(f"Invalid payment status: {payment_status}")

            if payment_status in ['PAID', 'PARTIALLY_REFUNDED'] and amount is None:
                raise RestValidationError("Amount is required for PAID or PARTIALLY_REFUNDED status")

            booking.payment_status = payment_status
            booking.last_modified_by = user
            booking.save()

            # Log action and notify
            action = f"PAYMENT_UPDATED to {payment_status}"
            if amount:
                action += f" (Amount: {amount})"
            BookingService._log_booking_action(booking, user, action)
            BookingService._notify_guest_booking_status_change(booking, f"payment updated to {payment_status}", amount)
            BookingService._notify_host_booking_status_change(booking, f"payment updated to {payment_status}")

            logger.info(f"Payment status for booking {booking.booking_id} updated to {payment_status} by {user.email}")
            return booking

    @staticmethod
    def complete_booking(booking: Booking, user: CustomUser) -> Booking:
        """
        Marks a booking as completed (admin-only, post-check-out).
        """
        with transaction.atomic():
            if not user.is_staff:
                raise PermissionDenied("Only admins can complete bookings")

            if booking.booking_status != 'CONFIRMED':
                raise RestValidationError("Only confirmed bookings can be completed")

            if timezone.now().date() < booking.end_date.date():
                raise RestValidationError("Booking cannot be completed before the end date")

            booking.booking_status = 'COMPLETED'
            booking.last_modified_by = user
            booking.save()

            # Log action and notify
            BookingService._log_booking_action(booking, user, "COMPLETED")
            BookingService._notify_guest_booking_status_change(booking, "completed")
            BookingService._notify_host_booking_status_change(booking, "completed")

            logger.info(f"Booking {booking.booking_id} completed by {user.email}")
            return booking

    @staticmethod
    def _generate_date_range(start_date: datetime, end_date: datetime) -> List[str]:
        """
        Generates a list of date strings between start_date and end_date (inclusive).
        """
        delta = end_date - start_date
        return [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]

    @staticmethod
    def _update_listing_availability(listing: Listing, date_range: List[str], available: bool):
        """
        Updates the availability JSON field for the specified date range.
        """
        for date_str in date_range:
            listing.availability[date_str] = available

    @staticmethod
    def _calculate_refunded_amount(booking: Booking) -> Decimal:
        """
        Calculates the refund amount based on the booking's payment status and cancellation policy.
        """
        if booking.payment_status in ['PENDING', 'FAILED']:
            return Decimal('0.00')

        if booking.listing.cancellation_policy == 'non_refundable':
            return Decimal('0.00')

        if booking.cancellation_deadline and timezone.now() <= booking.cancellation_deadline:
            return booking.total_amount  # type: ignore # Full refund within cancellation period

        # Partial refund for strict policy (base price only)
        if booking.listing.cancellation_policy == 'strict':
            return booking.total_amount - booking.service_fee - booking.tax_amount # type: ignore

        return booking.total_amount  # type: ignore # Full refund for flexible/moderate policies

    @staticmethod
    def _notify_guest_booking_status_change(booking: Booking, action: str, amount: Optional[Decimal] = None):
        """
        Notifies the guest of a booking status change or payment update.
        """
        try:
            message = (
                f"Dear {booking.user.first_name},\n\n"
                f"Your booking for {booking.listing.name} "
                f"from {booking.start_date.strftime('%Y-%m-%d %H:%M')} to {booking.end_date.strftime('%Y-%m-%d %H:%M')} "
                f"has been {action}.\n"
                f"Current Status: {booking.booking_status}\n"
                f"Payment Status: {booking.payment_status}\n"
            )
            if amount is not None:
                message += f"\nAmount: {amount}"

            send_mail(
                subject=f"Booking Update: {booking.listing.name}",
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[booking.user.email],
                fail_silently=False,
            )
            logger.info(f"Guest notification sent to {booking.user.email} for booking {booking.booking_id} ({action})")
        except Exception as e:
            logger.error(f"Failed to send guest notification for booking {booking.booking_id}: {str(e)}")
            raise

    @staticmethod
    def _notify_host_booking_status_change(booking: Booking, action: str):
        """
        Notifies the host of a booking status change.
        """
        try:
            send_mail(
                subject=f"Booking Update: {booking.listing.name}",
                message=(
                    f"Dear {booking.listing.host.first_name},\n\n"
                    f"The booking for your listing '{booking.listing.name}' "
                    f"by {booking.user.first_name} {booking.user.last_name} "
                    f"from {booking.start_date.strftime('%Y-%m-%d %H:%M')} to {booking.end_date.strftime('%Y-%m-%d %H:%M')} "
                    f"has been {action}.\n"
                    f"Current Status: {booking.booking_status}\n"
                    f"Payment Status: {booking.payment_status}\n"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[booking.listing.host.email],
                fail_silently=False,
            )
            logger.info(f"Host notification sent to {booking.listing.host.email} for booking {booking.booking_id} ({action})")
        except Exception as e:
            logger.error(f"Failed to send host notification for booking {booking.booking_id}: {str(e)}")
            raise

    @staticmethod
    def _log_booking_action(booking: Booking, user: CustomUser, action: str):
        """
        Logs booking actions for auditing.
        """
        logger.info(
            f"Booking {booking.booking_id} - Action: {action} by {user.email} "
            f"(Role: {user.user_role}, Status: {booking.booking_status}, Payment: {booking.payment_status})"
        )
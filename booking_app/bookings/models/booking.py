from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as gis_models
import uuid
from users.models.appuser import CustomUser
from listings.models.listing import Listing
from django.utils import timezone

class Booking(models.Model):
    """
    Stores bookings for listings in a modular structure.
    Focuses on data persistence and basic validation; business logic is handled in the service layer.
    Only users with role 'guest' can book; management is delegated to services.
    """
    booking_id = models.UUIDField(primary_key=True, 
                                default=uuid.uuid4,
                                editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE,
                                related_name='bookings')
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role': 'guest'},
        related_name='guest_bookings'
    )
    guests = models.PositiveIntegerField(
        default=1,
        help_text="Number of guests (must not exceed listing capacity)"
    )
    start_date = models.DateTimeField(null=False, blank=False)
    end_date = models.DateTimeField(null=False, blank=False)
    booking_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('CANCELLED', 'Cancelled'),
            ('COMPLETED', 'Completed')
        ],
        default='PENDING',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PAID', 'Paid'),
            ('FAILED', 'Failed'),
            ('PARTIALLY_REFUNDED', 'Partially Refunded'),
            ('FULLY_REFUNDED', 'Fully Refunded')
        ],
        default='PENDING',
        null=False,
        blank=False
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount including taxes and fees (set by service layer)"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Tax amount applied to the booking (set by service layer)"
    )
    service_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Service fee charged by the platform (set by service layer)"
    )
    cancellation_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deadline for free cancellation (set by service layer)"
    )
    special_requests = models.TextField(
        null=True,
        blank=True,
        help_text="Guest special requests (e.g., early check-in)"
    )
    is_instant_book = models.BooleanField(
        default=False,
        help_text="Booking is instantly confirmed without host approval"
    )
    last_modified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_bookings'
    )
    activation_code = models.CharField(max_length=50, blank=True, null=True)
    activation_code_expiry = models.DateTimeField(blank=True, null=True)

    def clean(self):
        """
        Performs basic validation:
        - End date must be after start date.
        - Number of guests must not exceed listing capacity.
        - No overlapping bookings for the same listing.
        Complex availability and policy checks are handled in the service layer.
        """
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")
        if self.guests > self.listing.capacity:
            raise ValidationError(f"Number of guests ({self.guests}) exceeds listing capacity ({self.listing.capacity}).")
        overlapping = Booking.objects.filter(
            listing=self.listing,
            end_date__gt=self.start_date,
            start_date__lt=self.end_date,
            booking_status__in=['PENDING', 'CONFIRMED']
        ).exclude(booking_id=self.booking_id)
        if overlapping.exists():
            raise ValidationError("This listing is already booked for the selected dates.")

    def save(self, *args, **kwargs):
        """Saves the instance after basic validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['listing', 'start_date', 'end_date']),
            models.Index(fields=['user', 'booking_status']),
            models.Index(fields=['payment_status']),
        
        ]
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            )
        ]

    def __str__(self):
        return f"Booking {self.booking_id} for {self.listing.name} by {self.user.first_name} ({self.booking_status})"
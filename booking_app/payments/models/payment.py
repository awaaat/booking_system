from django.db import models
from django.core.exceptions import ValidationError
import uuid
from users.models.appuser import CustomUser
from bookings.models.booking import Booking
from django.utils import timezone

class Payment(models.Model):
    """
    Stores payment details for bookings, designed for a senior-level booking platform.
    Supports multiple payments per booking (e.g., deposit, balance) and various statuses.
    Focuses on data persistence and basic validation; business logic is handled in the service layer.
    """
    payment_id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments', help_text="The booking associated with this payment")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_payments', help_text="The user who made the payment")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Total amount paid (including taxes and fees)"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Tax component of the payment (set by service layer)"
    )
    service_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Service fee component of the payment (set by service layer)"
    )
    payment_date = models.DateTimeField(default=timezone.now, help_text="Date and time the payment was processed")
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('CREDIT_CARD', 'Credit Card'),
            ('CHAPA', 'Chapa'),
            ('PAYPAL', 'PayPal'),
            ('MOBILE_MONEY', 'Mobile Money'),
            ('STRIPE', 'Stripe'),
            ('BANK_TRANSFER', 'Bank Transfer')
        ],
        null=False,
        blank=False,
        help_text="Method used for the payment"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PAID', 'Paid'),
            ('FAILED', 'Failed'),
            ('PARTIALLY_REFUNDED', 'Partially Refunded'),
            ('FULLY_REFUNDED', 'Fully Refunded'),
            ('PROCESSING', 'Processing')
        ],
        default='PENDING',
        null=False,
        blank=False,
        help_text="Current status of the payment"
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique identifier from the payment gateway"
    )
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount refunded, if any (set by service layer)"
    )
    refund_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time the refund was processed"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency of the payment (e.g., USD, EUR)"
    )
    last_modified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_payments',
        help_text="User who last modified the payment"
    )

    def clean(self):
        """
        Performs basic validation:
        - Ensures amount is positive.
        - Ensures refund_amount does not exceed the original amount.
        - Validates currency format.
        Complex payment processing and refund logic is handled in the service layer.
        """
        if self.amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        if self.refund_amount > self.amount:
            raise ValidationError("Refund amount cannot exceed the original payment amount.")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValidationError("Currency must be a three-letter code (e.g., USD, EUR).")

    def save(self, *args, **kwargs):
        """Saves the instance after basic validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['booking', 'payment_date']),
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['transaction_id']),
        ]
        ordering = ['-payment_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name='positive_payment_amount'
            ),
            models.CheckConstraint(
                check=models.Q(refund_amount__lte=models.F('amount')),
                name='refund_amount_not_exceed_payment'
            ),
        ]

    def __str__(self):
        return f"Payment {self.payment_id} for Booking {self.booking.booking_id} ({self.payment_status})"
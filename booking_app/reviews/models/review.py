from django.db import models
from django.core.exceptions import ValidationError
import uuid
from users.models.appuser import CustomUser
from listings.models.listing import Listing
from bookings.models.booking import Booking
from django.utils import timezone

class Review(models.Model):
    """
    Stores reviews for listings based on bookings, mirroring Booking.com functionality.
    Focuses on data persistence and basic validation; business logic is handled in the service layer.
    Only guests who have completed a booking can leave a review.
    """
    review_id = models.UUIDField(primary_key=True, db_index=True,
                                default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE,
                                related_name='reviews', help_text="The booking associated with this review")
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role': 'guest'},
        related_name='guest_reviews',
        help_text="The guest who wrote the review"
    )
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE,
                            related_name='reviews', help_text="The listing being reviewed")
    review_date = models.DateTimeField(default=timezone.now, help_text="Date the review was submitted")
    review_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Overall rating (1.0 to 10.0), set by service layer if not provided"
    )
    cleanliness_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Cleanliness rating (1.0 to 10.0)"
    )
    location_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Location rating (1.0 to 10.0)"
    )
    comfort_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Comfort rating (1.0 to 10.0)"
    )
    facilities_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Facilities rating (1.0 to 10.0)"
    )
    staff_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Staff rating (1.0 to 10.0)"
    )
    value_for_money_rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Value for money rating (1.0 to 10.0)"
    )
    comment = models.TextField(
        null=True,
        blank=True,
        help_text="Guest's written review"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether the review has been approved by the host or admin"
    )
    host_response = models.TextField(
        null=True,
        blank=True,
        help_text="Host's response to the review"
    )
    response_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date the host responded"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Whether the review is publicly visible"
    )
    last_modified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_reviews',
        help_text="User who last modified the review"
    )

    def clean(self):
        """
        Performs basic validation:
        - Ensures the booking is completed or checked out.
        - Ensures ratings are within 1.0 to 10.0 if provided.
        - Prevents duplicate reviews for the same booking.
        Complex approval and visibility logic is handled in the service layer.
        """
        if self.booking and self.booking.booking_status not in ['COMPLETED']:
            raise ValidationError("Reviews can only be submitted for completed bookings.")
        if self.review_rating is not None and not (1.0 <= self.review_rating <= 10.0):
            raise ValidationError("Overall rating must be between 1.0 and 10.0.")
        for field in ['cleanliness_rating', 'location_rating', 'comfort_rating', 'facilities_rating', 'staff_rating', 'value_for_money_rating']:
            if getattr(self, field) is not None and not (1.0 <= getattr(self, field) <= 10.0):
                raise ValidationError(f"{field.replace('_', ' ').title()} must be between 1.0 and 10.0.")
        if Review.objects.filter(booking=self.booking).exclude(review_id=self.review_id).exists():
            raise ValidationError("A review for this booking already exists.")

    def save(self, *args, **kwargs):
        """Saves the instance after basic validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['booking', 'review_date']),
            models.Index(fields=['user', 'is_approved']),
            models.Index(fields=['listing', 'is_public']),
        ]
        ordering = ['-review_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(review_rating__gte=1.0) & models.Q(review_rating__lte=10.0) |
                    models.Q(review_rating__isnull=True),
                name='valid_review_rating_range'
            ),
        ]

    def __str__(self):
        return f"Review {self.review_id} for {self.listing.name} by {self.user.first_name}"
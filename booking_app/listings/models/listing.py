from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as gis_models
import uuid
from users.models.appuser import CustomUser


class Listing(models.Model):
    """
    A property that can be booked. Only users with role 'host' can create listings.
    Includes geospatial location, detailed amenities, accessibility features, and availability tracking.
    Supports all Booking.com features and additional enhancements for a robust platform.
    """
    PROPERTY_TYPES = (
        ('apartment', 'Apartment'),
        ('hotel', 'Hotel'),
        ('guest_house', 'Guest House'),
        ('homestay', 'Homestay'),
        ('villa', 'Villa'),
        ('holiday_home', 'Holiday Home'),
        ('hostel', 'Hostel'),
        ('capsule_hotel', 'Capsule Hotel'),
        ('resort', 'Resort'),
        ('holiday_park', 'Holiday Park'),
        ('boat', 'Boat'),
        ('lodge', 'Lodge'),
        ('love_hotel', 'Love Hotel'),
    )

    REVIEW_SCORES = (
        ('superb', 'Superb: 9+'),
        ('very_good', 'Very Good: 8+'),
        ('good', 'Good: 7+'),
        ('pleasant', 'Pleasant: 6+'),
    )

    STAR_RATINGS = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )

    CANCELLATION_POLICIES = (
        ('flexible', 'Flexible'),
        ('moderate', 'Moderate'),
        ('strict', 'Strict'),
        ('non_refundable', 'Non-Refundable'),
    )

    property_id = models.UUIDField(primary_key=True,
                                default=uuid.uuid4,
                                editable=False)
    host = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role': 'host'},
        related_name='property_host'
    )
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    location = gis_models.PointField(geography=True, null=False, blank=False,
                                help_text="Geospatial coordinates (longitude, latitude)")
    address = models.CharField(max_length=200, null=True, blank=True,
                            help_text="Street address of the property")
    city = models.CharField(max_length=100, null=False, blank=False)
    country = models.CharField(max_length=100, null=False, blank=False)
    distance_from_center = models.FloatField(null=True, blank=True,
                                            help_text="Distance from city center in kilometers")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2,
                                        null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    capacity = models.PositiveIntegerField(null=False, blank=False, default=1,
                                        help_text="Maximum number of guests")
    bedrooms = models.PositiveIntegerField(default=1, help_text="Number of bedrooms")
    bathrooms = models.PositiveIntegerField(default=1, help_text="Number of bathrooms")
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES, default='apartment')
    average_review_score = models.FloatField(null=True, blank=True,
                                            help_text="Average review score (1-10)")
    review_count = models.PositiveIntegerField(default=0, help_text="Number of approved reviews")
    star_rating = models.PositiveSmallIntegerField(choices=STAR_RATINGS, null=True, blank=True)
    sustainability_certified = models.BooleanField(default=False,
                                                help_text="Property has sustainability certification")
    is_beachfront = models.BooleanField(default=False, help_text="Property is beachfront")
    is_entire_place = models.BooleanField(default=False, help_text="Entire home/apartment")
    pets_allowed = models.BooleanField(default=False, help_text="Pets are allowed")
    adults_only = models.BooleanField(default=False, help_text="Adults-only property")
    check_in_time = models.TimeField(null=True, blank=True, help_text="Check-in time")
    check_out_time = models.TimeField(null=True, blank=True, help_text="Check-out time")
    cancellation_policy = models.CharField(max_length=20,
                                        choices=CANCELLATION_POLICIES, default='flexible')
    house_rules = models.TextField(null=True, 
                                blank=True, help_text="House rules (e.g., no smoking, no parties)")
    child_policy = models.TextField(null=True, blank=True, 
                                help_text="Child policy (e.g., age restrictions, extra charges)")

    # Amenities (comprehensive to match Booking.com)
    amenities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed amenities (e.g., {'wifi': true, 'pool': false, 'air_conditioning': true})"
    )

    # Room facilities
    room_facilities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Room-specific facilities (e.g., {'sea_view': true, 'private_bathroom': false})"
    )

    # Accessibility features
    accessibility_features = models.JSONField(
        default=dict,
        blank=True,
        help_text="Accessibility features (e.g., {'wheelchair_accessible': true, 'toilet_with_grab_rails': false})"
    )

    # Activities and nearby attractions
    activities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Activities available (e.g., {'diving': true, 'golf_course': false})"
    )

    # Nearby landmarks
    landmarks = models.JSONField(
        default=dict,
        blank=True,
        help_text="Nearby landmarks with distances (e.g., {'Haller Park': 1.3, 'Fort Jesus': 0.7})"
    )

    availability = models.JSONField(
        default=dict,
        blank=True,
        help_text="Availability calendar (e.g., {'2025-06-01': true})"
    )
    check_in_instructions = models.TextField(
        null=True,
        blank=True,
        help_text="Instructions for check-in (e.g., access code)"
    )

    def clean(self):
        # Basic validations
        if not self.name.strip():
            raise ValidationError("Property name cannot be empty")
        if self.capacity < 1:
            raise ValidationError("Capacity must be at least 1")
        if not self.description.strip():
            raise ValidationError("Description cannot be empty")
        if self.price_per_night <= 0:
            raise ValidationError("Price cannot be 0.00 or less")
        if not self.address.strip() or not self.city.strip() or not self.country.strip(): # type: ignore
            raise ValidationError("Address, city, and country cannot be empty")
        if self.bedrooms < 0:
            raise ValidationError("Number of bedrooms cannot be negative")
        if self.bathrooms < 0:
            raise ValidationError("Number of bathrooms cannot be negative")
        if self.average_review_score is not None and not (1 <= self.average_review_score <= 10):
            raise ValidationError("Average review score must be between 1 and 10")
        if self.review_count < 0:
            raise ValidationError("Review count cannot be negative")

        # Uniqueness check
        if Listing.objects.filter(
            host=self.host,
            name=self.name.strip(),
            address=self.address.strip(), # type: ignore
            city=self.city.strip()
        ).exclude(pk=self.pk).exists():
            raise ValidationError("Property listing already exists at this address")

    def update_review_stats(self):
        """
        Updates average_review_score and review_count based on approved reviews.
        """
        from reviews.models.review import Review
        reviews = Review.objects.filter(listing=self, is_approved=True)
        self.review_count = reviews.count()
        self.average_review_score = reviews.aggregate(models.Avg('review_rating'))['review_rating__avg'] or None
        self.save()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['host', 'city', 'country']),
            models.Index(fields=['property_type']),
            models.Index(fields=['average_review_score']),
            models.Index(fields=['star_rating']),
            gis_models.Index(fields=['location'])
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.city}, {self.country}"


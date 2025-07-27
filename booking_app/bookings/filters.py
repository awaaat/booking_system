from django_filters import FilterSet, DateTimeFilter, CharFilter, NumberFilter, BooleanFilter, ChoiceFilter
from bookings.models.booking import Booking
from django import forms


class BookingFilter(FilterSet):
    """FilterSet for Booking model, supporting filtering by status, dates, and other fields."""
    # Text filters
    listing_name = CharFilter(field_name='listing__name', lookup_expr='icontains', help_text="Filter by listing name (case-insensitive)")
    user_email = CharFilter(field_name='user__email', lookup_expr='icontains', help_text="Filter by user email (case-insensitive)")
    special_requests = CharFilter(lookup_expr='icontains', help_text="Filter by special requests (case-insensitive)")

    # Status filters
    booking_status = ChoiceFilter(choices=Booking.booking_status.field.choices, help_text="Filter by booking status (e.g., PENDING, CONFIRMED)") # type: ignore
    payment_status = ChoiceFilter(choices=Booking.payment_status.field.choices, help_text="Filter by payment status (e.g., PENDING, PAID)") # type: ignore

    # Date range filters
    start_date_gte = DateTimeFilter(field_name='start_date', lookup_expr='gte', help_text="Filter by start date greater than or equal to")
    start_date_lte = DateTimeFilter(field_name='start_date', lookup_expr='lte', help_text="Filter by start date less than or equal to")
    end_date_gte = DateTimeFilter(field_name='end_date', lookup_expr='gte', help_text="Filter by end date greater than or equal to")
    end_date_lte = DateTimeFilter(field_name='end_date', lookup_expr='lte', help_text="Filter by end date less than or equal to")
    created_at_gte = DateTimeFilter(field_name='created_at', lookup_expr='gte', help_text="Filter by creation date greater than or equal to")
    created_at_lte = DateTimeFilter(field_name='created_at', lookup_expr='lte', help_text="Filter by creation date less than or equal to")

    # Number range filters
    guests_gte = NumberFilter(field_name='guests', lookup_expr='gte', help_text="Filter by minimum number of guests")
    guests_lte = NumberFilter(field_name='guests', lookup_expr='lte', help_text="Filter by maximum number of guests")
    total_amount_gte = NumberFilter(field_name='total_amount', lookup_expr='gte', help_text="Filter by minimum total amount")
    total_amount_lte = NumberFilter(field_name='total_amount', lookup_expr='lte', help_text="Filter by maximum total amount")
    tax_amount_gte = NumberFilter(field_name='tax_amount', lookup_expr='gte', help_text="Filter by minimum tax amount")
    tax_amount_lte = NumberFilter(field_name='tax_amount', lookup_expr='lte', help_text="Filter by maximum tax amount")
    service_fee_gte = NumberFilter(field_name='service_fee', lookup_expr='gte', help_text="Filter by minimum service fee")
    service_fee_lte = NumberFilter(field_name='service_fee', lookup_expr='lte', help_text="Filter by maximum service fee")

    # Boolean filter
    is_instant_book = BooleanFilter(field_name='is_instant_book', help_text="Filter by instant booking status")

    # Related field filters
    listing_id = CharFilter(field_name='listing__property_id', lookup_expr='exact', help_text="Filter by listing ID (UUID)")
    cancellation_policy = ChoiceFilter(field_name='listing__cancellation_policy', choices=Booking.listing.field.related_model.CANCELLATION_POLICIES, help_text="Filter by listing cancellation policy") # type: ignore

    class Meta:
        model = Booking
        fields = [
            'listing_name', 'user_email', 'special_requests',
            'booking_status', 'payment_status',
            'start_date_gte', 'start_date_lte', 'end_date_gte', 'end_date_lte',
            'created_at_gte', 'created_at_lte',
            'guests_gte', 'guests_lte',
            'total_amount_gte', 'total_amount_lte',
            'tax_amount_gte', 'tax_amount_lte',
            'service_fee_gte', 'service_fee_lte',
            'is_instant_book', 'listing_id', 'cancellation_policy'
        ]
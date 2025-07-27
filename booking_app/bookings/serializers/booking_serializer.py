from rest_framework import serializers
from django.utils import timezone
from users.serializers.user_serializer import CustomUserSerializer
from listings.serializers.listing_serializer import ListingSerializer
from bookings.models.booking import Booking

class BookingInputSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings."""
    listing_id = serializers.UUIDField()  # Input as UUID
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    guests = serializers.IntegerField(min_value=1)
    special_requests = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    is_instant_book = serializers.BooleanField(default=False)
    

    class Meta:
        model = Booking
        fields = ['listing_id', 'start_date', 'end_date', 
                'guests', 'special_requests', 
                'is_instant_book']

    def validate(self, data):
        """Validate start_date is in the future."""
        if data['start_date'] < timezone.now():
            raise serializers.ValidationError("Start date must be in the future")
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data

class BookingOutputSerializer(serializers.ModelSerializer):
    """Serializer for retrieving booking details."""
    user = CustomUserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    last_modified_by = CustomUserSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Booking
        fields = [
            'booking_id', 'user', 'listing', 'guests', 'start_date', 'end_date',
            'booking_status', 'payment_status', 'total_amount', 'tax_amount',
            'service_fee', 'cancellation_deadline', 'special_requests',
            'is_instant_book', 'created_at',
            'updated_at', 'last_modified_by'
        ]

class PaymentUpdateSerializer(serializers.Serializer):
    """Serializer for updating payment status."""
    payment_status = serializers.ChoiceField(choices=[choice[0] for choice in Booking.payment_status.field.choices]) # type: ignore
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate(self, data):
        """Ensure amount is provided for specific payment statuses."""
        if data['payment_status'] in ['PAID', 'PARTIALLY_REFUNDED'] and data.get('amount') is None:
            raise serializers.ValidationError("Amount is required for PAID or PARTIALLY_REFUNDED status")
        return data
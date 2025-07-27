from rest_framework import serializers
from reviews.models.review import Review
from users.serializers.user_serializer import CustomUserSerializer
from listings.models.listing import Listing, PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    """
    Serializer for PropertyImage model to handle multiple images.
    """
    class Meta:
        model = PropertyImage
        fields = ('image', 'alt_text', 'uploaded_at')
        read_only_fields = ('uploaded_at',)


class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for Listing model, including all Booking.com-like features.
    """
    host = CustomUserSerializer(read_only=True)
    property_images = PropertyImageSerializer(many=True, read_only=True)
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = (
            'property_id',
            'host',
            'name',
            'description',
            'location',
            'address',
            'city',
            'country',
            'distance_from_center',
            'price_per_night',
            'created_at',
            'updated_at',
            'property_images',
            'capacity',
            'bedrooms',
            'bathrooms',
            'property_type',
            'average_review_score',
            'review_count',
            'star_rating',
            'sustainability_certified',
            'is_beachfront',
            'is_entire_place',
            'pets_allowed',
            'adults_only',
            'check_in_time',
            'check_out_time',
            'cancellation_policy',
            'house_rules',
            'child_policy',
            'amenities',
            'room_facilities',
            'accessibility_features',
            'activities',
            'landmarks',
            'availability',
            'reviews',
        )
        read_only_fields = (
            'property_id',
            'host',
            'created_at',
            'updated_at',
            'average_review_score',
            'review_count',
            'property_images',
            'reviews',
        )

    def validate_amenities(self, value):
        """
        Validate amenities JSON structure.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Amenities must be a dictionary")
        return value

    def validate_room_facilities(self, value):
        """
        Validate room_facilities JSON structure.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Room facilities must be a dictionary")
        return value

    def validate_accessibility_features(self, value):
        """
        Validate accessibility_features JSON structure.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Accessibility features must be a dictionary")
        return value

    def validate_activities(self, value):
        """
        Validate activities JSON structure.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Activities must be a dictionary")
        return value

    def validate_landmarks(self, value):
        """
        Validate landmarks JSON structure.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Landmarks must be a dictionary")
        for key, val in value.items():
            if not isinstance(val, (int, float)):
                raise serializers.ValidationError("Landmark distances must be numbers")
        return value

    def validate_availability(self, value):
        """
        Validate availability JSON structure.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Availability must be a dictionary")
        return value

    def validate(self, data):
        """
        Additional validation for related fields.
        """
        if data.get('capacity', 1) < 1:
            raise serializers.ValidationError({"capacity": "Capacity must be at least 1"})
        if data.get('price_per_night', 0) <= 0:
            raise serializers.ValidationError({"price_per_night": "Price cannot be 0.00 or less"})
        if data.get('bedrooms', 0) < 0:
            raise serializers.ValidationError({"bedrooms": "Number of bedrooms cannot be negative"})
        if data.get('bathrooms', 0) < 0:
            raise serializers.ValidationError({"bathrooms": "Number of bathrooms cannot be negative"})
        return data
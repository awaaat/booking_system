from rest_framework import serializers # type: ignore
from rest_framework_gis.serializers import GeometryField # type: ignore
from users.serializers.user_serializer import CustomUserSerializer
from listings.models.listing import Listing
from listings.models.property_images import PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ('image', 'alt_text', 'uploaded_at')
        read_only_fields = ('uploaded_at',)

class ListingSerializer(serializers.ModelSerializer):
    host = CustomUserSerializer(read_only=True)
    property_images = PropertyImageSerializer(many=True, read_only=True)
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    #Edit reviews to include what the user only needs to see
    location = GeometryField()  # Handle GeoJSON Point
    
    
    class Meta:
        model = Listing
        fields = (
            'property_id', 'host', 'name', 'description', 'location', 'address', 'city',
            'country', 'distance_from_center', 'price_per_night', 'created_at', 'updated_at',
            'property_images', 'capacity', 'bedrooms', 'bathrooms', 'property_type',
            'average_review_score', 'review_count', 'star_rating', 'sustainability_certified',
            'is_beachfront', 'is_entire_place', 'pets_allowed', 'adults_only',
            'check_in_time', 'check_out_time', 'cancellation_policy', 'house_rules',
            'child_policy', 'amenities', 'room_facilities', 'accessibility_features',
            'activities', 'landmarks', 'availability', 'reviews', 'check_in_instructions'
        )
        read_only_fields = (
            'property_id', 'host', 'created_at', 'updated_at', 'average_review_score',
            'review_count', 'property_images', 'reviews', 'check_in_instructions'
        )

    def validate_amenities(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Amenities must be a dictionary")
        return value

    def validate_room_facilities(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Room facilities must be a dictionary")
        return value

    def validate_accessibility_features(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Accessibility features must be a dictionary")
        return value

    def validate_activities(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Activities must be a dictionary")
        return value

    def validate_landmarks(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Landmarks must be a dictionary")
        for key, val in value.items():
            if not isinstance(val, (int, float)):
                raise serializers.ValidationError("Landmark distances must be numbers")
        return value

    def validate_availability(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Availability must be a dictionary")
        return value
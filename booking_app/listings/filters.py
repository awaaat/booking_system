from django_filters import FilterSet, DateTimeFilter, CharFilter, NumberFilter, BooleanFilter, ChoiceFilter
from listings.models.listing import Listing


class ListingFilter(FilterSet):
    # Text filters
    name = CharFilter(lookup_expr='icontains')
    address = CharFilter(lookup_expr='icontains')
    city = CharFilter(lookup_expr='icontains')
    country = CharFilter(lookup_expr='icontains')

    # Price range filters
    price_per_night_gte = NumberFilter(field_name='price_per_night', lookup_expr='gte')
    price_per_night_lte = NumberFilter(field_name='price_per_night', lookup_expr='lte')

    # Capacity and room count range filters
    capacity_gte = NumberFilter(field_name='capacity', lookup_expr='gte')
    capacity_lte = NumberFilter(field_name='capacity', lookup_expr='lte')
    bedrooms_gte = NumberFilter(field_name='bedrooms', lookup_expr='gte')
    bedrooms_lte = NumberFilter(field_name='bedrooms', lookup_expr='lte')
    bathrooms_gte = NumberFilter(field_name='bathrooms', lookup_expr='gte')
    bathrooms_lte = NumberFilter(field_name='bathrooms', lookup_expr='lte')

    # Date range filters
    created_at_gte = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = DateTimeFilter(field_name='created_at', lookup_expr='lte')

    # Review and rating filters
    average_review_score_gte = NumberFilter(field_name='average_review_score', lookup_expr='gte')
    average_review_score_lte = NumberFilter(field_name='average_review_score', lookup_expr='lte')
    review_count_gte = NumberFilter(field_name='review_count', lookup_expr='gte')
    review_count_lte = NumberFilter(field_name='review_count', lookup_expr='lte')
    star_rating = ChoiceFilter(choices=Listing.STAR_RATINGS)

    # Property type filter
    property_type = ChoiceFilter(choices=Listing.PROPERTY_TYPES)

    # Boolean filters for specific features
    sustainability_certified = BooleanFilter(field_name='sustainability_certified')
    is_beachfront = BooleanFilter(field_name='is_beachfront')
    is_entire_place = BooleanFilter(field_name='is_entire_place')
    pets_allowed = BooleanFilter(field_name='pets_allowed')
    adults_only = BooleanFilter(field_name='adults_only')

    # Cancellation policy filter
    cancellation_policy = ChoiceFilter(choices=Listing.CANCELLATION_POLICIES)

    # JSONField (amenities) filters
    wifi = BooleanFilter(field_name='amenities__wifi')
    pool = BooleanFilter(field_name='amenities__pool')
    parking = BooleanFilter(field_name='amenities__parking')
    air_conditioning = BooleanFilter(field_name='amenities__air_conditioning')
    restaurant = BooleanFilter(field_name='amenities__restaurant')
    spa = BooleanFilter(field_name='amenities__spa')
    fitness_center = BooleanFilter(field_name='amenities__fitness_center')

    # Room facilities filters
    sea_view = BooleanFilter(field_name='room_facilities__sea_view')
    private_bathroom = BooleanFilter(field_name='room_facilities__private_bathroom')
    kitchen = BooleanFilter(field_name='room_facilities__kitchen')

    # Accessibility features filters
    wheelchair_accessible = BooleanFilter(field_name='accessibility_features__wheelchair_accessible')
    toilet_with_grab_rails = BooleanFilter(field_name='accessibility_features__toilet_with_grab_rails')

    # Activities filters
    beach = BooleanFilter(field_name='activities__beach')
    golf_course = BooleanFilter(field_name='activities__golf_course')

    class Meta:
        model = Listing
        fields = [
            'name', 'address', 'city', 'country',
            'price_per_night_gte', 'price_per_night_lte',
            'capacity_gte', 'capacity_lte',
            'bedrooms_gte', 'bedrooms_lte',
            'bathrooms_gte', 'bathrooms_lte',
            'created_at_gte', 'created_at_lte',
            'average_review_score_gte', 'average_review_score_lte',
            'review_count_gte', 'review_count_lte',
            'star_rating',
            'property_type',
            'sustainability_certified', 'is_beachfront', 'is_entire_place',
            'pets_allowed', 'adults_only',
            'cancellation_policy',
            'wifi', 'pool', 'parking', 'air_conditioning', 'restaurant',
            'spa', 'fitness_center',
            'sea_view', 'private_bathroom', 'kitchen',
            'wheelchair_accessible', 'toilet_with_grab_rails',
            'beach', 'golf_course',
        ]
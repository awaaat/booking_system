from django.urls import path, include
from rest_framework.routers import DefaultRouter # type: ignore
from rest_framework_nested.routers import NestedDefaultRouter # type: ignore
from listings.views.listing_views import ListingViewSet
from bookings.views.booking_views import BookingViewSet

router = DefaultRouter()
router.register(r'property_listings', ListingViewSet, basename='listing')

property_listings_router = NestedDefaultRouter(router, r'property_listings', lookup='listing')
#property_listings_router.register(r'bookings', BookingViewSet, basename='listing-bookings')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(property_listings_router.urls)),
]

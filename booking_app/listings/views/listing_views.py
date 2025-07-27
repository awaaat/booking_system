from rest_framework import viewsets, filters
from listings.models.listing import Listing
from listings.serializers.listing_serializer import ListingSerializer
from listings.filters import ListingFilter
from common.permissions.permissions import IsOwnerOrAdmin
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from listings.services.listing_service import ListingService
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from common.utils import CustomPagination


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    filterset_class = ListingFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'name', 'address', 'city', 'country', 'description',
        'price_per_night', 'capacity', 'property_type'
    ]
    ordering_fields = ['created_at', 'price_per_night', 'average_review_score', 'review_count']
    pagination_class = CustomPagination

    def get_queryset(self):
        """Retrieve listings using the service layer logic"""
        return ListingService.get_listings_for_user(self.request.user, queryset=self.queryset) # type: ignore

    def get_permissions(self):
        """Allows list/retrieve for any authenticated user; others restricted to hosts or admins"""
        return [IsOwnerOrAdmin()]

    def create(self, request, *args, **kwargs):
        """For hosts to create a new listing"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = ListingService.create_listing(
            user=request.user,
            data=serializer.validated_data
        )
        return Response(self.get_serializer(listing).data, status=201)

    def update(self, request, *args, **kwargs):
        """For updating a listing based on service layer logic"""
        listing = self.get_object()
        serializer = self.get_serializer(listing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_listing = ListingService.update_listing(
            user=request.user,
            listing=listing,
            data=serializer.validated_data
        )
        return Response(self.get_serializer(updated_listing).data)

    def destroy(self, request, *args, **kwargs):
        """For deleting a listing"""
        listing = self.get_object()
        ListingService.delete_listing(user=request.user, listing=listing)
        return Response(status=204)
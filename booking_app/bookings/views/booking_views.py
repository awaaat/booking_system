import logging
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as RestValidationError
from django_filters.rest_framework import DjangoFilterBackend

from bookings.models.booking import Booking
from bookings.services.booking_service import BookingService
from bookings.serializers.booking_serializer import BookingInputSerializer, BookingOutputSerializer, PaymentUpdateSerializer
from common.permissions.permissions import IsOwnerOrAdmin
from common.utils import CustomPagination
from bookings.filters import BookingFilter


logger = logging.getLogger("bookings.views")

class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bookings."""
    queryset = Booking.objects.all()
    serializer_class = BookingOutputSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['listing__name', 'user__email', 'special_requests']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'total_amount']
    pagination_class = CustomPagination
    filterset_class = BookingFilter

    def get_queryset(self):
        """Retrieve bookings scoped to a specific listing if provided, respecting user roles."""
        listing_id = self.kwargs.get("listing_pk") or self.kwargs.get("property_listings_pk") or self.kwargs.get("listing_id")
        if listing_id:
            from listings.models.listing import Listing
            try:
                listing = Listing.objects.get(property_id=listing_id)
            except Listing.DoesNotExist:
                raise RestValidationError("Listing not found")

            return BookingService.get_bookings_for_user(self.request.user, listing)
        else:
            # Fallback if listing_id is not part of URL — only if you want to allow that.
            return Booking.objects.none()# type: ignore

    def get_permissions(self):
        """Apply IsOwnerOrAdmin for all actions except list/retrieve, which require IsAuthenticated."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsOwnerOrAdmin()]

    def get_serializer_class(self):
        """Use BookingInputSerializer for create, PaymentUpdateSerializer for payment update, BookingOutputSerializer for others."""
        if self.action == 'create':
            return BookingInputSerializer
        if self.action == 'update_payment':
            return PaymentUpdateSerializer
        return BookingOutputSerializer

    def create(self, request, *args, **kwargs):
        """Create a new booking for a guest."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = BookingService.create_booking(request.user, serializer.validated_data)
            return Response(
                {"booking_id": str(booking.booking_id), "message": "Booking created"},
                status=status.HTTP_201_CREATED
            )
        except (PermissionDenied, RestValidationError) as e:
            logger.error(f"Booking creation failed for {request.user.email}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single booking's details."""
        booking = self.get_object()
        if not (request.user.is_staff or booking.user == request.user or booking.listing.host == request.user):
            logger.error(f"Unauthorized access to booking {booking.booking_id} by {request.user.email}")
            raise PermissionDenied("No permission to view this booking")
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Cancel a booking."""
        booking = self.get_object()
        try:
            BookingService.cancel_booking(request.user, booking)
            return Response(
                {"booking_id": str(booking.booking_id), "message": "Booking cancelled"},
                status=status.HTTP_200_OK
            )
        except (PermissionDenied, RestValidationError) as e:
            logger.error(f"Booking cancellation failed for {booking.booking_id}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def confirm(self, request, pk=None, code=None):
        """Confirm a booking with activation code."""
        try:
            booking = BookingService.confirm_booking(pk, code) # type: ignore
            return Response(
                {"booking_id": str(booking.booking_id), "message": "Booking confirmed"},
                status=status.HTTP_200_OK
            )
        except RestValidationError as e:
            logger.error(f"Booking confirmation failed for {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update_payment(self, request, pk=None):
        """Update payment status (admin-only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = BookingService.get_booking_by_id(pk)
            booking = BookingService.update_payment_status(
                booking, serializer.validated_data['payment_status'], request.user, serializer.validated_data.get('amount')
            )
            return Response(
                {"booking_id": str(booking.booking_id), "message": "Payment status updated"},
                status=status.HTTP_200_OK
            )
        except (PermissionDenied, RestValidationError) as e:
            logger.error(f"Payment update failed for {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def complete(self, request, pk=None):
        """Mark a booking as completed (admin-only)."""
        try:
            booking = BookingService.get_booking_by_id(pk) # type: ignore
            booking = BookingService.complete_booking(booking, request.user)
            return Response(
                {"booking_id": str(booking.booking_id), "message": "Booking completed"},
                status=status.HTTP_200_OK
            )
        except (PermissionDenied, RestValidationError) as e:
            logger.error(f"Booking completion failed for {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
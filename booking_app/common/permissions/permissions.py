from rest_framework.permissions import BasePermission # type: ignore
from listings.models.listing import Listing
from bookings.models.booking import Booking
from users.models.appuser import CustomUser


class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission class to enforce role-based access control:
    - Listings are public (all authenticated users can view).
    - For other resources (e.g., bookings), users can only access their own data.
    - Hosts can only access their own listings for non-list/retrieve actions.
    - Admins (is_staff=True) have full access to all resources.
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated and has general permission for the action.
        """
        # Enforce IsAuthenticated for all actions
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins have full access
        if request.user.is_staff:
            return True

        # Allow all authenticated users to list or retrieve listings
        if view.action in ['list', 'retrieve'] and view.basename == 'listing':
            return True

        # For other resources or actions (e.g., create, update, destroy), defer to object-level permission
        return True

    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions:
        - Listings: Allow all authenticated users to view (retrieve).
        - Bookings: Only allow the guest who made the booking or admins.
        - Listings (non-retrieve): Only allow the host who owns the listing or admins.
        - Other resources: Only allow the user who owns the resource or admins.
        """
        # Admins have full access
        if request.user.is_staff:
            return True

        # Listings are public for retrieve
        if isinstance(obj, Listing) and view.action == 'retrieve':
            return True

        # For bookings, only the guest who made the booking
        if isinstance(obj, Booking):
            return obj.user == request.user

        # For listings (non-retrieve actions, e.g., update, destroy), only the host who owns it
        if isinstance(obj, Listing):
            return obj.host == request.user

        # For other resources (e.g., CustomUser or other models), check if the object is the user
        if isinstance(obj, CustomUser):
            return obj == request.user
        
        # Default: Deny access if no specific rule applies
        return False
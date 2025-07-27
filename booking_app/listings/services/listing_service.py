from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.db.models import QuerySet, Avg, ObjectDoesNotExist # type: ignore
from django.contrib.gis.geos import Point
from listings.models.listing import Listing
from listings.models.property_images import PropertyImage # type: ignore
from users.models.appuser import CustomUser
from reviews.models.review import Review
from rest_framework.exceptions import ValidationError as RestValidationError
from django.contrib.gis.geos import GEOSGeometry

class ListingService:
    """
    A class that contains the logic for listings, including creating, updating, and deleting.
    Handles all Booking.com-like features and ensures role-based permissions.
    """
    @staticmethod
    def get_listings_for_user(user: CustomUser, queryset: QuerySet) -> QuerySet:
        """
        Retrieve listings based on user roles.
        Staff see all listings, hosts see their own, guests see all available listings.
        """
        if not queryset:
            queryset = Listing.objects.all()
        if not user.is_authenticated:
            raise PermissionDenied("You do not have permission to view listings")
        
        if user.is_staff:
            return queryset
        elif user.user_role == 'host':
            return queryset.filter(host=user)
        elif user.user_role == 'guest':
            return queryset.filter(availability__isnull=False)  # Only show listings with availability
        raise PermissionDenied("Invalid user role")

    @staticmethod
    def create_listing(user: CustomUser, data: dict) -> Listing:
        """
        Create a new listing for a host, handling geospatial and image data.
        """
        if user.user_role != 'host':
            raise PermissionDenied("You do not have permissions to perform this action")
        if 'location' in data:
            try:
                data['location'] = GEOSGeometry(str(data['location']), srid=4326)
            except Exception as e:
                raise RestValidationError(f"Invalid location format: {str(e)}")
        else:
            raise RestValidationError("Location is required")

        # Extract image data if provided
        image_data = data.pop('property_images', [])

        # Create listing
        listing = Listing(host=user, **data)
        listing.full_clean()
        listing.save()

        # Handle property images
        for image in image_data:
            PropertyImage.objects.create(
                listing=listing,
                image=image.get('image'),
                alt_text=image.get('alt_text', '')
            )

        return listing

    @staticmethod
    def update_listing(user: CustomUser, listing: Listing, data: dict) -> Listing:
        """
        Update an existing listing, ensuring only the host or admin can modify it.
        Handles geospatial and image updates.
        """
        if user.user_role != 'host' or listing.host != user:
            if not user.is_staff:
                raise PermissionDenied("Only the property owner or admin can update this listing")

        # Handle geospatial location update
        longitude = data.pop('longitude', None)
        latitude = data.pop('latitude', None)
        if longitude is not None and latitude is not None:
            try:
                data['location'] = Point(float(longitude), float(latitude), srid=4326)
            except (ValueError, TypeError):
                raise RestValidationError("Invalid longitude or latitude values")

        # Handle property images update
        if 'property_images' in data:
            image_data = data.pop('property_images')
            # Optionally clear existing images
            if data.get('clear_images', False):
                PropertyImage.filter(listing = listing).delete()
            for image in image_data:
                PropertyImage.objects.create(
                    listing=listing,
                    image=image.get('image'),
                    alt_text=image.get('alt_text', '')
                )

        # Update listing fields
        for attr, value in data.items():
            setattr(listing, attr, value)

        listing.full_clean()
        listing.save()
        return listing

    @staticmethod
    def delete_listing(user: CustomUser, listing: Listing) -> None:
        """
        Delete a listing, ensuring only the host or admin can perform the operation.
        """
        if not (user.is_staff or (user.user_role == 'host' and listing.host == user)):
            raise PermissionDenied("Only the property owner or admin can delete this listing")
        listing.delete()

    @staticmethod
    def get_listing_by_id(listing_id: str) -> Listing:
        """
        Retrieve a single listing by its ID.
        """
        try:
            return Listing.objects.get(property_id=listing_id)
        except ObjectDoesNotExist:
            raise RestValidationError("Listing does not exist")
        except Exception as e:
            raise RestValidationError(f"Error: Invalid listing ID - {str(e)}")

    @staticmethod
    def update_review_stats(listing: Listing) -> None:
        """
        Update the listing's average_review_score and review_count based on approved reviews.
        """
        reviews = Review.objects.filter(listing=listing, is_approved=True)
        listing.review_count = reviews.count()
        listing.average_review_score = reviews.aggregate(Avg('review_rating'))['review_rating__avg'] or None
        listing.save()
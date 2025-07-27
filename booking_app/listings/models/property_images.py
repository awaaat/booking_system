from django.db import models
import uuid
from listings.models.listing import Listing

class PropertyImage(models.Model):
    """
    Stores images related to a single property listing.
    Each image belongs to exactly one listing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='property_images',
        help_text="The listing this image belongs to"
    )

    image = models.ImageField(
        upload_to='property_images/',
        default='property_images/default.jpg',
        help_text="Image file of the property"
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility and SEO"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.listing.name} ({self.listing.property_id})"

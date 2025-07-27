from django.db import models
from django.core.exceptions import ValidationError
import uuid
from users.models.appuser import CustomUser
from listings.models.listing import Listing
from django.utils import timezone

class Conversation(models.Model):
    """
    Represents a direct conversation between a guest and a host for a specific listing.
    Supports one-to-one messaging; not designed for group chats.
    Focuses on data persistence and basic validation; business logic is handled in the service layer.
    """
    conversation_id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='conversations', help_text="The listing related to this conversation")
    guest = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role': 'guest'},
        related_name='guest_conversations',
        help_text="The guest participating in the conversation"
    )
    host = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role': 'host'},
        related_name='host_conversations',
        help_text="The host participating in the conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time the conversation was started")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time of the last message or update")
    is_active = models.BooleanField(default=True, help_text="Whether the conversation is active or archived")

    def clean(self):
        """
        Performs basic validation:
        - Ensures guest and host are different users.
        - Ensures the host is the listing's owner.
        Complex participant management is handled in the service layer.
        """
        if self.guest == self.host:
            raise ValidationError("Guest and host cannot be the same user.")
        if self.listing and self.host != self.listing.host:
            raise ValidationError("Host must be the owner of the related listing.")

    def save(self, *args, **kwargs):
        """Saves the instance after basic validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['listing', 'created_at']),
            models.Index(fields=['guest', 'host']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['guest', 'host', 'listing'], name='unique_conversation_per_guest_host_listing'),
        ]

    def __str__(self):
        return f"Conversation {self.conversation_id} between {self.guest.first_name} and {self.host.first_name} for {self.listing.name}"
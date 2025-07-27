from django.db import models
from django.core.exceptions import ValidationError
import uuid
from users.models.appuser import CustomUser
from messaging.models.conversation import Conversation
from django.utils import timezone

class Message(models.Model):
    """
    Represents a message within a conversation between a guest and a host.
    Focuses on data persistence and basic validation; business logic is handled in the service layer.
    """
    message_id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', help_text="The conversation this message belongs to")
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role__in': ['guest', 'host']},
        related_name='sent_messages',
        help_text="The user who sent the message"
    )
    receiver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_role__in': ['guest', 'host']},
        related_name='received_messages',
        help_text="The user intended to receive the message"
    )
    message_content = models.TextField(null=False, blank=False, help_text="The content of the message")
    timestamp = models.DateTimeField(default=timezone.now, help_text="Date and time the message was sent")
    read = models.BooleanField(default=False, help_text="Whether the message has been read by the receiver")
    edited = models.BooleanField(default=False, help_text="Whether the message has been edited")

    def clean(self):
        """
        Performs basic validation:
        - Ensures sender and receiver are part of the conversation.
        - Ensures message content is not empty.
        Complex delivery and read status logic is handled in the service layer.
        """
        if self.conversation and self.sender not in [self.conversation.guest, self.conversation.host]:
            raise ValidationError("Sender must be the guest or host of the conversation.")
        if self.conversation and self.receiver not in [self.conversation.guest, self.conversation.host]:
            raise ValidationError("Receiver must be the guest or host of the conversation.")
        if not self.message_content.strip():
            raise ValidationError("Message content cannot be empty.")

    def save(self, *args, **kwargs):
        """Saves the instance after basic validation and updates conversation timestamp."""
        self.full_clean()
        if not self._state.adding:  # Only update if not a new instance
            self.conversation.updated_at = timezone.now()
            self.conversation.save()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender', 'read']),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"Message {self.message_id} in {self.conversation.conversation_id} by {self.sender.first_name}"
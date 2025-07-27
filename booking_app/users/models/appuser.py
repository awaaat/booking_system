from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import re


phone_regex = RegexValidator(
    r'^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3,4})[-. )]*(\d{3})[-. ]*(\d{3,4})(?: *x(\d+))?\s*$',
    message="Phone number must be in the format: '+999999999'. Up to 15 digits allowed."
)

class CustomUser(AbstractUser):
    """
    Represents a user in the application. Can be a guest, host, or admin.
    Uses UUID for primary key and includes timezone-aware fields.
    """
    class Meta:
        db_table = "app_user"

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100, null=False, blank=False)
    last_name = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(null=False, blank=False, unique=True)
    phone_number = models.CharField(max_length=50, null=False, blank=False, validators=[phone_regex])
    user_role = models.CharField(
        choices=[('guest', 'Guest'), ('host', 'Host'), ('admin', 'Admin')],
        max_length=50, default='guest', null=False, blank=False
    )
    created_at = models.DateTimeField(default=timezone.now)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, 
                                    null=True, default='profiles/default.png')
    is_email_verified = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=50, blank=True, null=True)
    activation_code_expiry = models.DateTimeField(blank=True, null=True)

    def clean(self):
        # This is a custom validation for user model
        if not self.first_name.isalpha() or not self.last_name.isalpha():
            raise ValidationError("First name and last name should only contain letters")
        if self.user_role =='admin' and not self.is_staff:
            raise ValidationError("Admin users must have is_staff=True")
        if self.bio and len(self.bio) > 500:
            raise ValidationError("Bio cannot exceed 500 characters")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user_role})"

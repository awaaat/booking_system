import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone

from users.models.appuser import CustomUser

logger = logging.getLogger("users")

class UserRegistrationService:
    
    @staticmethod
    def user_exists(email):
        """Checks if the user already exists in the system"""
        if CustomUser.objects.filter(email=email).exists():
            return True
        return False

    @staticmethod
    def username_exists(username):
        """Checks if the user already exists in the system"""
        if CustomUser.objects.filter(username = username).exists():
            return True
        return False
    @staticmethod
    def create_user(data, is_active=False):
        """Creates a user with an activation code"""
        user = CustomUser.objects.create_user(
            email=data['email'],
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            user_role=data['user_role'],
            bio=data.get('bio', ''),
            profile_image=data.get('profile_image'),
        )
        user.is_active = False
        user.is_email_verified = False
        user.activation_code = secrets.token_urlsafe(32)
        user.activation_code_expiry = timezone.now() + timedelta(minutes=10)
        user.save()
        return user

    @staticmethod
    def send_verification_email(user):
        """Sends verification email with activation url"""
        try:
            verification_url = f"{settings.SITE_URL}/api/auth/verify/{user.user_id}/{user.activation_code}"
            send_mail(
                subject="Activate Your Account",
                message=f"Click the url to attached to this message to activate your account: {verification_url}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            raise

    @staticmethod
    def activate_user(user_id, code):
        """Activates user if valid code is provided"""
        try:
            user = CustomUser.objects.get(user_id=user_id)
            if user.activation_code_expiry and user.activation_code_expiry < timezone.now():
                raise ValueError("Activation code expired")
            if user.activation_code != code:
                raise ValueError("Invalid activation code")
            user.is_active = True
            user.is_email_verified = True
            user.activation_code = ''
            user.activation_code_expiry = None
            user.save()
            logger.info(f"User with email {user.email} activated")
            return True
        except CustomUser.DoesNotExist:
            logger.error(f"User with user_id {user_id} not found")
            raise ValueError("User not found")
        except Exception as e:
            logger.error(f"Activation failed: {str(e)}")
            raise

    @staticmethod
    def send_password_reset_email(user):
        """Sends instructions for password reset"""
        if not user.is_email_verified:
            raise ValueError("Please verify your email before resetting password")
        try:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.user_id))
            reset_url = f"{settings.SITE_URL}/api/auth/reset/{uid}/{token}"
            send_mail(
                subject="Reset Your Password",
                message=f"Click to reset your password: {reset_url}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            raise
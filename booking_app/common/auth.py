from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.views import TokenObtainPairView
from typing import Dict, Any 

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    This serializer customizes the data included in the token that is returned when a user logs in.
    It adds extra information to the token (like the username and user_id) so that the frontend
    or client can use it without making extra API calls to retrieve basic user info.
    """

    @classmethod
    def get_token(cls, user):
        """
        This method is called when the token is being generated.
        It adds custom fields to the token payload.

        Parameters:
        user (ChatUser): The user who is logging in. This comes from your custom user model.

        Returns:
        token: A JWT token that includes the extra fields.
        """
        token = super().get_token(user)

        # Add extra data to the token payload
        token['username'] = user.username  # Username can be used on frontend for display
        token['user_id'] = str(user.user_id)  # Custom user_id from your ChatUser model

        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    This view uses the custom serializer above to return the token during login.
    It ensures that the extra user information is included in the response.
    """
    serializer_class = CustomTokenObtainPairSerializer

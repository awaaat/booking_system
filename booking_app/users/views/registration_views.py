from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from users.models.appuser import CustomUser
from users.serializers.registration_serializer import UserRegistrationSerializer
from users.serializers.user_serializer import CustomUserSerializer
from users.services.user_registration_service import UserRegistrationService

class RegisterAPI(generics.CreateAPIView):
    """API endpoint for user registration"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        data = serializer.validated_data
        try:
            user = UserRegistrationService.create_user(data)
            UserRegistrationService.send_verification_email(user)
            return Response({
                'user_id': str(user.user_id),
                'message': 'User created, check email for activation code'
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailAPI(generics.GenericAPIView):
    """API endpoint to verify email with activation token via GET request"""
    permission_classes = [AllowAny]

    def get(self, request, user_id, token):
        try:
            if UserRegistrationService.activate_user(user_id, token):
                return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
from rest_framework import serializers
from users.services.user_registration_service import UserRegistrationService
from users.models.appuser import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'user_id',
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'user_role',
            'bio',
            'profile_image',
            'password',
            'password_confirm',
        ]
        read_only_fields = ['user_id']
        
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        if UserRegistrationService.user_exists(data['email']):
            raise serializers.ValidationError("A user with that email already exists")
        if UserRegistrationService.username_exists(data['username']):
            raise serializers.ValidationError("A user with a similar username already exists")
        return data

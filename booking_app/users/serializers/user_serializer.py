from rest_framework import serializers
from users.models.appuser import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            'user_id',
            'first_name',
            'last_name',
            'phone_number',
            'profile_image',
            'user_role',
            'bio',
        )
        read_only_fields = ['user_id']

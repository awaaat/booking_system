from rest_framework import viewsets, filters # type: ignore
from rest_framework.permissions import IsAuthenticated, IsAdminUser # type: ignore
from common.permissions.permissions import IsOwnerOrAdmin
from users.models.appuser import CustomUser
from users.serializers.user_serializer import CustomUserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for managing users"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name']
    ordering_fields = ['date_joined']
    permission_classes = [IsOwnerOrAdmin]
    
    def get_permissions(self):
        """Custom permissions: Allow list/retrieve for authenticated users, others for admins"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(user_id=user.user_id)
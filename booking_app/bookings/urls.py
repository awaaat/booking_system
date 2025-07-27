from django.urls import path, include
from rest_framework.routers import DefaultRouter # type: ignore
from bookings.views.booking_views import BookingViewSet

app_name = 'bookings'

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
    path('bookings/<str:pk>/confirm/<str:code>/', BookingViewSet.as_view({'post': 'confirm'}), name='booking-confirm'),
    path('bookings/<str:pk>/payment/', BookingViewSet.as_view({'post': 'update_payment'}), name='booking-payment-update'),
    path('bookings/<str:pk>/complete/', BookingViewSet.as_view({'post': 'complete'}), name='booking-complete'),
]
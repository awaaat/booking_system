from django.urls import path, include
from rest_framework import routers # type: ignore
from rest_framework_nested.routers import NestedDefaultRouter # type: ignore

from users.views.user_views import UserViewSet
from users.views.registration_views import RegisterAPI, VerifyEmailAPI
from bookings.views.booking_views import BookingViewSet
from listings.views.listing_views import ListingViewSet
#from payments.views.payment_views import PaymentViewSet
#from reviews.views.review_views import ReviewViewSet
#from messaging.views.conversation_views import ConversationViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

user_router = NestedDefaultRouter(router, r'users', lookup='user')
user_router.register(r'bookings', BookingViewSet, basename='user-bookings')
#user_router.register(r'reviews', ReviewViewSet, basename='user-reviews')
#user_router.register(r'payments', PaymentViewSet, basename='user-payments')
user_router.register(r'listings', ListingViewSet, basename='user-listings')
#user_router.register(r'conversations', ConversationViewSet, basename='user-conversations')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(user_router.urls)),
    path('auth/register/', RegisterAPI.as_view(), name='api-register'),
    path('auth/verify/<uuid:user_id>/<str:token>/', VerifyEmailAPI.as_view(), name='verify_email'),
]
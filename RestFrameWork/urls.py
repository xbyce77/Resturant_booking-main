from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    ViewReservationView,
    CreateAPIReservationView,
    UpdateReservationView,
    autocomplete_table_name,
    check_table_availability,
)

urlpatterns = [
    # JWT token endpoints for authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API endpoints for reservations
    path('', ViewReservationView.as_view(), name='reservation-list'),
    path('create/', CreateAPIReservationView.as_view(), name='reservation-create'),
    path('update/<int:pk>/', UpdateReservationView.as_view(), name='reservation-update'),

    # Autocomplete endpoint for table names (likely an AJAX GET)
    path('autocomplete-table/', autocomplete_table_name, name='autocomplete-table'),
    path('api/check-table-availability/', check_table_availability, name='check-table-availability'),
]

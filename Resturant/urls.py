from django.urls import path
from . import views  
from .views import (
    RegistrationView,
    CreateReservationView,
    LoginView,
    LogoutView,
    DjangoLogoutView,
    ViewReservationView,
    UpdateReservationView,
    DeleteReservationView,
    home_view,
    reviews_view,
    add_to_table,
    MenuDetailView,
    add_to_cart,
    view_cart,
    check_availability,
    MenuListView,
    search_menu,
)

urlpatterns = [
    # Authentication
    path('register/', RegistrationView.as_view(), name='register'), 
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Home & Static Pages
    path('',views.home_view, name='home'), 
    path('reviews/create/', reviews_view, name='reviews'),

    # Reservation Management
    path('create-reservation/', CreateReservationView.as_view(), name='create-reservation'),

    path('display-reservation/', ViewReservationView.as_view(), name='view-reservation'),
    path('update-reservation/<int:pk>/', UpdateReservationView.as_view(), name='update-reservation'),
    path('delete-reservation/<int:pk>/', DeleteReservationView.as_view(), name='delete-reservation'),
    path('menulist/', MenuListView.as_view(), name='menu-list'),


    # Menu & Cart
    path('menu/', views.search_menu, name='menu-search'),
    path('menu/<int:pk>/', MenuDetailView.as_view(), name='menu_detail'),
    path('menu/<int:pk>/add-to-cart/', add_to_cart, name='add_to_cart'),
    path('cart/',view_cart, name='view_cart'),

    # Table Orders
    path('reservation/<int:reservation_id>/add-to-table/', add_to_table, name='add-to-table'),

    # Search
    path('search/', views.search_menu, name='search-menu'),
    path('cart/add-to-reservation/<int:reservation_id>/', views.add_cart_to_table, name='add_cart_to_table'),
    path('check-availability/', views.check_availability, name='check-availability')

]
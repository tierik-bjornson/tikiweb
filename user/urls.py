from django.urls import path
from .views import RegisterView, LoginView, UserView, UpdateAvatarView, UpdateProfileView
from .custom_token import CustomTokenObtainPairView 
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("user/", UserView.as_view(), name="user"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path('update-profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('update-avatar/', UpdateAvatarView.as_view(), name='update_avatar'),
]

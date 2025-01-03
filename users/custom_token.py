from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, users):
        token = super().get_token(users)

        token['username'] = users.username
        token['email'] = users.email
        token['is_staff'] = users.is_staff
        token['is_superuser'] = users.is_superuser
        token['id'] = users.id
        token['avatar'] = users.avatar.url if users.avatar else None
        if users.is_superuser:
            token['role'] = "ADMIN"
        else :
            token['role'] = "CUSTOMER"
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
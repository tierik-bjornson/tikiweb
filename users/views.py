import base64

from django.core.files.base import ContentFile
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerialize, LoginSerialize
from .models import User
from .custom_token import CustomTokenObtainPairSerializer
class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerialize(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerialize(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data
            token = CustomTokenObtainPairSerializer.get_token(user)
            return Response({
                'refresh': str(token),
                'access': str(token.access_token),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        avatar_data = request.data.get('avatar')

        if avatar_data:
            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'avatar.{ext}')
            if user.avatar:
                user.avatar.delete()

            user.avatar.save(f'avatar_{user.id}.{ext}', data, save=True)

            serializer = UserSerializer(user)
            return Response(serializer.data)

        return Response({'error': 'No avatar data provided'}, status=status.HTTP_400_BAD_REQUEST)
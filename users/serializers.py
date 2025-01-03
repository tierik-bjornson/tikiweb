from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(format = "%Y-%m-%d", input_formats=['%Y-%m-%dT', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ'])
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_of_birth', 'phone_number', 'purchase_address', 'delivery_address', 'avatar']

class RegisterSerialize(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'date_of_birth', 'phone_number', 'purchase_address', 'delivery_address']
    def create(seft, validate_date):
        user = User.objects.create_user(**validate_date)
        return user

class LoginSerialize(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField()
    def validate(seft, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")
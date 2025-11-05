from rest_framework import serializers
from django.contrib.auth.models import User

# Define the LoginSerializer
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

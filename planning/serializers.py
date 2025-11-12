from rest_framework import serializers
from .models import XerImportJob


class XerImportSerializer(serializers.Serializer):
    xer_file = serializers.FileField()


class XerImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = XerImportJob
        fields = ['id', 'status', 'message', 'summary', 'created_at', 'completed_at']
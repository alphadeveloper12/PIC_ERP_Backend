from rest_framework import serializers
from .models import P6Activity, PrimaveraSheet

class PrimaveraSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrimaveraSheet
        fields = '__all__'

class P6ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = P6Activity
        fields = '__all__'
from rest_framework import serializers
from .models import *

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class RevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revision
        fields = '__all__'


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'


class BillItemSerializer(serializers.ModelSerializer):
    # Adding material field to BillItemSerializer
    materials = MaterialSerializer(many=True)

    class Meta:
        model = BillItem
        fields = '__all__'


class AppConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppConfigKV
        fields = '__all__'

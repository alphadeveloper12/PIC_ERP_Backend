from rest_framework import serializers
from .models import Project, SubPhase
from core.serializers import CompanySerializer


class ProjectSerializer(serializers.ModelSerializer):
    # company = CompanySerializer(required=False)

    class Meta:
        model = Project
        fields = '__all__'


class SubPhaseSerializer(serializers.ModelSerializer):
    # project = ProjectSerializer()

    class Meta:
        model = SubPhase
        fields = '__all__'

from .models import Estimation, BOQ, Section, Subsection, BOQItem
from rest_framework import serializers
from core.serializers import ProfileSerializer
from projects.serializers import SubPhaseSerializer


class EstimationSerializer(serializers.ModelSerializer):
    # subphase = SubPhaseSerializer()
    # prepared_by = ProfileSerializer()
    # approved_by = ProfileSerializer()

    class Meta:
        model = Estimation
        fields = '__all__'


class BOQSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)

    class Meta:
        model = BOQ
        fields = ['id', 'name', 'file_path', 'file_hash']


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'name']


class SubsectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subsection
        fields = ['id', 'name']


class BOQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOQItem
        fields = ['id', 'description', 'unit', 'quantity', 'rate', 'amount']


class DetailedSubsectionSerializer(serializers.ModelSerializer):
    items = BOQItemSerializer(many=True)

    class Meta:
        model = Subsection
        fields = ['id', 'name', 'items']


class DetailedSectionSerializer(serializers.ModelSerializer):
    subsections = DetailedSubsectionSerializer(many=True)

    class Meta:
        model = Section
        fields = ['id', 'name', 'subsections']


class BOQDetailSerializer(serializers.ModelSerializer):
    sections = DetailedSectionSerializer(many=True)

    class Meta:
        model = BOQ
        fields = ['id', 'name', 'sections']

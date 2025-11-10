from .models import *
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
        fields = ['id', 'name','factor', 'subsections']


class BOQDetailSerializer(serializers.ModelSerializer):
    sections = DetailedSectionSerializer(many=True)

    class Meta:
        model = BOQ
        fields = ['id', 'name', 'sections']


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'


class BOQItemCostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOQItem
        fields = [
            "id",
            "description",
            "labor_hours",
            "labor_amount",
            "plant_rate",
            "plant_amount",
            "subcontract_rate",
            "subcontract_amount",
            "dry_cost",
            "unit_rate",
            "boq_amount",
        ]
        read_only_fields = [
            "subcontract_amount",
            "dry_cost",
            "unit_rate",
            "boq_amount",
        ]

    def update(self, instance, validated_data):
        """
        Update only provided fields, then trigger recalculation
        via BOQItem.save().
        """
        for field, value in validated_data.items():
            setattr(instance, field, value)

        # save() already recalculates everything in your model
        instance.save()
        return instance
from .models import *
from rest_framework import serializers
from core.serializers import ProfileSerializer
from projects.serializers import SubPhaseSerializer


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'


class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'


class LabourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Labour
        fields = '__all__'


class SubcontractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcontract
        fields = '__all__'


class EstimationSerializer(serializers.ModelSerializer):
    sub_phase = serializers.PrimaryKeyRelatedField(
        queryset=SubPhase.objects.all(), source='subphase', write_only=True
    )

    class Meta:
        model = Estimation
        fields = '__all__'
        extra_kwargs = {
            'subphase': {'read_only': True}
        }

    def to_internal_value(self, data):
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = data['status'].upper()
        return super().to_internal_value(data)


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
    materials = MaterialSerializer(many=True, read_only=True)
    plant_rate = serializers.SerializerMethodField()
    plant_amount = serializers.SerializerMethodField()
    labour_hours = serializers.SerializerMethodField()
    labour_amount = serializers.SerializerMethodField()
    labour_unit_rate = serializers.SerializerMethodField()
    subcontract_rate = serializers.SerializerMethodField()
    subcontract_amount = serializers.SerializerMethodField()
    section_name = serializers.SerializerMethodField()
    section_factor = serializers.SerializerMethodField()
    total_amount = serializers.FloatField(source='boq_amount', read_only=True)
    uses_section_factor = serializers.SerializerMethodField()
    saved_at_iso = serializers.SerializerMethodField()

    class Meta:
        model = BOQItem
        fields = [
            'id', 'description', 'unit', 'quantity', 'rate', 'amount',
            'materials', 'plant_rate', 'plant_amount', 
            'labour_hours', 'labour_amount', 'labour_unit_rate',
            'subcontract_rate', 'subcontract_amount',
            'dry_cost', 'unit_rate', 'factor', 'prelimin', 'total_amount',
            'section_name', 'section_factor', 'uses_section_factor', 'saved_at_iso'
        ]

    def get_plant_rate(self, obj):
        plant = obj.plants.first()
        return plant.rate if plant else 0

    def get_plant_amount(self, obj):
        plant = obj.plants.first()
        return plant.amount if plant else 0

    def get_labour_hours(self, obj):
        labour = obj.labours.first()
        return labour.hours if labour else 0

    def get_labour_amount(self, obj):
        labour = obj.labours.first()
        return labour.amount if labour else 0

    def get_labour_unit_rate(self, obj):
        labour = obj.labours.first()
        if labour and labour.hours and labour.amount:
            return labour.amount / labour.hours
        return 0

    def get_subcontract_rate(self, obj):
        sub = obj.subcontracts.first()
        return sub.rate if sub else 0

    def get_subcontract_amount(self, obj):
        sub = obj.subcontracts.first()
        return sub.amount if sub else 0

    def get_section_name(self, obj):
        return obj.subsection.section.name if obj.subsection and obj.subsection.section else ""

    def get_section_factor(self, obj):
        return obj.subsection.section.factor if obj.subsection and obj.subsection.section else 0
    
    def get_uses_section_factor(self, obj):
        return True # Hardcoded as per upsert logic, or derive if needed

    def get_saved_at_iso(self, obj):
        return None


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
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Supplier, DMApproval, RawMaterial, Inventory,
    ProcurementOrder, QCResult, MixDesign, CostElement, ApprovalWorkflow
)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username  # Django auth needs username
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data['user'] = user
        return data


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class DMApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DMApproval
        fields = '__all__'


class RawMaterialSerializer(serializers.ModelSerializer):
    primary_supplier = SupplierSerializer(read_only=True)
    primary_supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source='primary_supplier', write_only=True
    )

    class Meta:
        model = RawMaterial
        fields = '__all__'


class InventorySerializer(serializers.ModelSerializer):
    material = RawMaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=RawMaterial.objects.all(), source='material', write_only=True
    )

    class Meta:
        model = Inventory
        fields = '__all__'


class ProcurementOrderSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source='supplier', write_only=True
    )
    material = RawMaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=RawMaterial.objects.all(), source='material', write_only=True
    )

    class Meta:
        model = ProcurementOrder
        fields = '__all__'


class QCResultSerializer(serializers.ModelSerializer):
    material = RawMaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=RawMaterial.objects.all(), source='material', write_only=True
    )

    class Meta:
        model = QCResult
        fields = '__all__'


class MixDesignSerializer(serializers.ModelSerializer):
    material = RawMaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=RawMaterial.objects.all(), source='material', write_only=True
    )

    class Meta:
        model = MixDesign
        fields = '__all__'


class CostElementSerializer(serializers.ModelSerializer):
    material = RawMaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=RawMaterial.objects.all(), source='material', write_only=True
    )

    class Meta:
        model = CostElement
        fields = '__all__'


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    material = RawMaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=RawMaterial.objects.all(), source='material', write_only=True
    )

    class Meta:
        model = ApprovalWorkflow
        fields = '__all__'
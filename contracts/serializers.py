from rest_framework import serializers
from .models import ConstructionContract, ContractClause

class ContractClauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractClause
        fields = ['id', 'category', 'original_text', 'interpreted_value', 'page_number']

class ConstructionContractSerializer(serializers.ModelSerializer):
    clauses = ContractClauseSerializer(many=True, read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = ConstructionContract
        fields = '__all__'
        read_only_fields = ['uploaded_at', 'uploaded_by', 'is_processed']

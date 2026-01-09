from rest_framework import serializers
from .models import Department, WorkflowPhase, WorkflowStep, Task, Document, UserDepartmentRole
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class WorkflowPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowPhase
        fields = '__all__'

class WorkflowStepSerializer(serializers.ModelSerializer):
    actor_department_code = serializers.CharField(source='actor_department.code', read_only=True)
    receiver_department_code = serializers.CharField(source='receiver_department.code', read_only=True)
    
    class Meta:
        model = WorkflowStep
        fields = '__all__'

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    workflow_step_details = WorkflowStepSerializer(source='workflow_step', read_only=True)
    assigned_to_details = UserSimpleSerializer(source='assigned_to', read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'completed_at']

    def validate_assigned_to(self, value):
        # Ensure the assigned user belongs to the actor department of the step
        # This could be expensive to check every time, maybe skip or optimize
        return value

class TaskActionSerializer(serializers.Serializer):
    """
    Serializer for actions like Assign, Approve, Reject
    """
    action = serializers.ChoiceField(choices=['ASSIGN', 'APPROVE', 'REJECT', 'SUBMIT'])
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    comments = serializers.CharField(required=False, allow_blank=True)

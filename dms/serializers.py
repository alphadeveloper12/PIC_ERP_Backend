from rest_framework import serializers
from .models import Department, WorkflowPhase, WorkflowStep, Task, Document, UserDepartmentRole, AccessPolicy
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

class UserDepartmentRoleSerializer(serializers.ModelSerializer):
    user_details = UserSimpleSerializer(source='user', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    
    class Meta:
        model = UserDepartmentRole
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
    p6_activity_name = serializers.SerializerMethodField()
    related_documents = serializers.SerializerMethodField()
    early_start = serializers.CharField(source='linked_p6_activity.first.early_start', read_only=True)
    early_finish = serializers.CharField(source='linked_p6_activity.first.early_finish', read_only=True)
    late_start = serializers.CharField(source='linked_p6_activity.first.late_start', read_only=True)
    late_finish = serializers.CharField(source='linked_p6_activity.first.late_finish', read_only=True)
    actual_start = serializers.CharField(source='linked_p6_activity.first.actual_start', read_only=True)
    actual_finish = serializers.CharField(source='linked_p6_activity.first.actual_finish', read_only=True)

    def get_p6_activity_name(self, obj):
        act = obj.linked_p6_activity.first()
        return act.activity_name if act else None

    def get_related_documents(self, obj):
        # Fetch documents from the parent task chain
        docs = []
        curr = obj.parent_task
        visited = set()
        while curr and curr.id not in visited:
            visited.add(curr.id)
            for doc in curr.documents.all():
                docs.append(DocumentSerializer(doc).data)
            curr = curr.parent_task
        return docs
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'completed_at']
        extra_kwargs = {
            'workflow_step': {'required': False, 'allow_null': True}
        }

    def validate_assigned_to(self, value):
        return value

class TaskActionSerializer(serializers.Serializer):
    """
    Serializer for actions like Assign, Approve, Reject
    """
    action = serializers.ChoiceField(choices=['ASSIGN', 'APPROVE', 'REJECT', 'SUBMIT', 'START'])
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    comments = serializers.CharField(required=False, allow_blank=True)

class AccessPolicySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    project_code = serializers.CharField(source='project.code', read_only=True)
    
    class Meta:
        model = AccessPolicy
        fields = '__all__'

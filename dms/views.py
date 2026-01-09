from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Department, Task, Document, WorkflowStep
from .serializers import DepartmentSerializer, TaskSerializer, DocumentSerializer, TaskActionSerializer
from django.utils import timezone
from django.db.models import Count, Q

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Tasks properly scoped by Project.
    Includes custom actions for workflow transitions (Assign, Approve, etc.).
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['project__name', 'workflow_step__action_description']
    ordering_fields = ['created_at', 'status', 'project__code']

    def get_queryset(self):
        """
        Filters tasks by:
        1. project_id (mandatory/optional depending on context)
        2. mode: 'my_tasks' (assigned to user) or 'department' (user's department role)
        """
        qs = super().get_queryset()
        
        # Filter by Project ID
        project_id = self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)
            
        # Filter by Mode
        mode = self.request.query_params.get('mode')
        if mode == 'my_tasks':
            qs = qs.filter(assigned_to=self.request.user)
        elif mode == 'department':
            # Identify departments where the user has a role
            user_depts = self.request.user.department_roles.values_list('department', flat=True)
            if user_depts:
                # Show tasks where the Actor is one of user's departments
                # This logic ensures users see tasks waiting for their department's action
                qs = qs.filter(workflow_step__actor_department__in=user_depts)
        
        return qs

    @action(detail=True, methods=['post'], serializer_class=TaskActionSerializer)
    def perform_action(self, request, pk=None):
        """
        Executes a workflow action on a task.
        Supported actions: ASSIGN, SUBMIT, APPROVE, REJECT.
        """
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        comments = serializer.validated_data.get('comments', '')
        assignee = serializer.validated_data.get('assigned_to')

        if action_type == 'ASSIGN':
            if not assignee:
                return Response(
                    {'error': 'assigned_to is required for ASSIGN action'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            task.assigned_to = assignee
            task.status = 'ASSIGNED'

        elif action_type == 'SUBMIT':
            task.status = 'SUBMITTED'

        elif action_type == 'APPROVE':
            task.status = 'APPROVED'
            task.completed_at = timezone.now()
            # Signal will handle creating the next task automatically

        elif action_type == 'REJECT':
            task.status = 'REJECTED'
        
        if comments:
            task.comments = comments
            
        task.save()
        return Response(TaskSerializer(task).data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Returns aggregated task statistics for dashboards.
        """
        queryset = self.get_queryset()
        
        stats = queryset.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='PENDING')),
            assigned=Count('id', filter=Q(status='ASSIGNED')),
            in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
            submitted=Count('id', filter=Q(status='SUBMITTED')),
            approved=Count('id', filter=Q(status='APPROVED')),
            rejected=Count('id', filter=Q(status='REJECTED')),
        )
        return Response(stats)

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

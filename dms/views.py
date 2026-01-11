from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Department, Task, Document, WorkflowStep
from .models import Department, Task, Document, WorkflowStep, UserDepartmentRole
from .serializers import (
    DepartmentSerializer, TaskSerializer, DocumentSerializer, 
    TaskActionSerializer, UserDepartmentRoleSerializer
)
from .services import WorkflowEngine, DocumentService
from django.utils import timezone
from django.db.models import Count, Q

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProjectTeamViewSet(viewsets.ModelViewSet):
    """
    Manages team members and their roles within departments.
    """
    queryset = UserDepartmentRole.objects.all()
    serializer_class = UserDepartmentRoleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'department__name', 'department__code']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Superuser sees everything. 
        # Others only see teams for projects they own.
        if not user.is_superuser:
            qs = qs.filter(project__owner_user=user)

        department_id = self.request.query_params.get('department_id')
        project_id = self.request.query_params.get('project_id')
        
        if department_id:
            qs = qs.filter(department_id=department_id)
        if project_id:
            qs = qs.filter(project_id=project_id)
            
        return qs


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
        
        # Admin / Owner Override to see everything
        if mode == 'all_tasks' and self.request.user.is_superuser:
             pass # No filter applied = show all
             
        elif mode == 'my_tasks':
            qs = qs.filter(assigned_to=self.request.user)
            
        elif mode == 'department':
            # Identify departments where the user has a role
            user_depts = self.request.user.department_roles.values_list('department', flat=True)
            
            # If user is superuser, maybe they should see everything in 'department' view too?
            # Or distinct 'all' view. Let's keep strict for department view.
            
            if user_depts:
                # Show tasks where the Actor is one of user's departments
                qs = qs.filter(workflow_step__actor_department__in=user_depts)
            else:
                # If user has no department, but is superuser, show all?
                if self.request.user.is_superuser:
                    pass
                else:
                    qs = qs.none()
        
        elif mode == 'project_owner':
            qs = qs.filter(project__owner_user=self.request.user)
        
        return qs

    @action(detail=True, methods=['post'], serializer_class=TaskActionSerializer)
    def perform_action(self, request, pk=None):
        """
        Executes a workflow action on a task using WorkflowEngine.
        Supported actions: ASSIGN, SUBMIT, APPROVE, REJECT.
        """
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        comments = serializer.validated_data.get('comments', '')
        assignee = serializer.validated_data.get('assigned_to')

        try:
            updated_task = WorkflowEngine.transition_task(
                task=task,
                action=action_type,
                user=request.user,
                comments=comments,
                assigned_to=assignee
            )
            return Response(TaskSerializer(updated_task).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        # We manually handle creation to use DocumentService
        # But perform_create expects to just save. 
        # Better to override create() or just let serializer save and then trigger service?
        # Let's override perform_create to delegate to service, but we need the file.
        # Actually, simpler to just start the task in perform_create if we trust serializer validation.
        
        # NOTE: standard perform_create does serializer.save(). 
        # We want to use DocumentService.upload_document which creates the instance.
        # So we bypass serializer.save() or wrap it.
        
        # Let's do:
        task = serializer.validated_data['task']
        document_type = serializer.validated_data.get('document_type', 'General')
        file = serializer.validated_data['file']
        
        DocumentService.upload_document(
            task=task,
            file=file,
            user=self.request.user,
            document_type=document_type
        )
        # Note: DocumentService creates the object, so we don't need to call serializer.save() 
        # But we need to return the instance for the response. 
        # This might break the standard ViewSet flow slightly if we don't return.
        # However, perform_create returns None. The create() method uses serializer.data.
        # Since we didn't call serializer.save(), serializer.instance is None.
        
        # Workaround: Let's simple hook into perform_create, let serializer save, then trigger async.
        instance = serializer.save(uploaded_by=self.request.user)
        
        # Trigger processing manually here if we don't want to use DocumentService.upload_document fully
        # OR better: Refactor DocumentService to accept instance.
        
        # Re-reading my plan: "DocumentService: upload_document(file, task) -> Saves file, triggers async AI processing."
        # If I want to stick to the plan:
        # I should override create() logic.
        pass

    def create(self, request, *args, **kwargs):
        # Override create to use Service
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        task = serializer.validated_data['task']
        file = serializer.validated_data['file']
        document_type = serializer.validated_data.get('document_type', 'General')
        
        doc = DocumentService.upload_document(
            task=task,
            file=file,
            user=request.user,
            document_type=document_type
        )
        
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

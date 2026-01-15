from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Department, Task, Document, WorkflowStep, UserDepartmentRole, AccessPolicy
from .serializers import (
    DepartmentSerializer, TaskSerializer, DocumentSerializer, 
    TaskActionSerializer, UserDepartmentRoleSerializer, AccessPolicySerializer
)
from .services import WorkflowEngine, DocumentService
from .permissions import HasRequiredPermission
from django.utils import timezone
from django.db.models import Count, Q, F
from projects.models import Project

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Department.objects.all()
        
        # Project Owners see all departments to seed them
        if Project.objects.filter(owner_user=user).exists():
            return Department.objects.all()
            
        # Others (HODs) only see departments they are part of as HOD or ADMIN
        return Department.objects.filter(
            members__user=user, 
            members__role__in=['HOD', 'ADMIN']
        ).distinct()

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
    permission_classes = [IsAuthenticated, HasRequiredPermission]
    required_permission = 'manage_team'
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'department__name', 'department__code']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Superuser sees everything. 
        # Others see teams for projects they own OR departments where they are HOD.
        if not user.is_superuser:
            qs = qs.filter(
                Q(project__owner_user=user) | 
                Q(department__members__user=user, department__members__role='HOD', department__members__project=F('project'))
            ).distinct()

        department_id = self.request.query_params.get('department_id')
        project_id = self.request.query_params.get('project_id')
        
        if department_id:
            qs = qs.filter(department_id=department_id)
        if project_id:
            qs = qs.filter(project_id=project_id)
            
        return qs

    @action(detail=False, methods=['GET'])
    def performance(self, request):
        user = request.user
        project_id = request.query_params.get('project_id')
        
        # Get departments where user is HOD
        hod_departments = UserDepartmentRole.objects.filter(
            user=user, role='HOD'
        ).values_list('department_id', flat=True)
        
        if not hod_departments and not user.is_superuser:
            return Response({"error": "You do not have HOD access to view performance."}, status=403)

        # Filter tasks
        tasks = Task.objects.filter(status='APPROVED', assigned_to__isnull=False)
        if project_id:
            tasks = tasks.filter(project_id=project_id)
        
        if not user.is_superuser:
            tasks = tasks.filter(workflow_step__actor_department_id__in=hod_departments)

        from planning.models import P6Activity
        
        performance_data = []
        
        # Aggregate by user
        assigned_users = tasks.values(
            'assigned_to', 
            'assigned_to__username', 
            'assigned_to__first_name', 
            'assigned_to__last_name'
        ).distinct()
        
        for u in assigned_users:
            user_tasks = tasks.filter(assigned_to_id=u['assigned_to'])
            total_completed = user_tasks.count()
            
            efficiency_days = 0
            tasks_with_p6 = 0
            
            for t in user_tasks:
                # Find linked P6 activity
                p6 = P6Activity.objects.filter(dms_task=t).first()
                if p6 and p6.early_finish and t.completed_at:
                    diff = (p6.early_finish - t.completed_at).days
                    efficiency_days += diff
                    tasks_with_p6 += 1
            
            kpi_score = (total_completed * 10) + (max(0, efficiency_days) * 5)
            
            performance_data.append({
                "user_id": u['assigned_to'],
                "username": u['assigned_to__username'],
                "full_name": f"{u['assigned_to__first_name']} {u['assigned_to__last_name']}",
                "tasks_completed": total_completed,
                "efficiency_days": efficiency_days,
                "tasks_with_p6": tasks_with_p6,
                "kpi_score": kpi_score
            })

        # Sort by KPI score
        performance_data = sorted(performance_data, key=lambda x: x['kpi_score'], reverse=True)

        return Response({
            "status": "success",
            "data": performance_data
        })


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Tasks properly scoped by Project.
    Includes custom actions for workflow transitions (Assign, Approve, etc.).
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, HasRequiredPermission]
    required_permission = 'view_tasks'
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

        if action_type == 'REJECT' and not comments:
            return Response({'error': 'Remarks are required when rejecting a task.'}, status=status.HTTP_400_BAD_REQUEST)

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
    permission_classes = [IsAuthenticated, HasRequiredPermission]
    required_permission = 'submit_tasks'

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

class AccessPolicyViewSet(viewsets.ModelViewSet):
    queryset = AccessPolicy.objects.all().select_related('department', 'project')
    serializer_class = AccessPolicySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Security: Non-superusers only see policies for:
        # 1. Projects they own
        # 2. Global templates (project=None)
        if not user.is_superuser:
            qs = qs.filter(Q(project__owner_user=user) | Q(project__isnull=True))

        project_id = self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)
             
        return qs.order_by('department__name', 'role')

    def get_permissions(self):
        # We allow viewing for authenticated, but mutation only for high-privilege
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), HasRequiredPermission()]
        return super().get_permissions()

    required_permission = 'manage_projects' # Project Owner permission

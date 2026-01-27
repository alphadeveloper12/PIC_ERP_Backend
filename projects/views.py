from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db.models import Q
from .models import Project, SubPhase, Company
from .serializers import ProjectSerializer, SubPhaseSerializer, CompanySerializer


class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        print("Received data:", request.data)
        try:
            serializer = ProjectSerializer(data=request.data)
            if serializer.is_valid():
                # Auto-assign the creator as the owner_user if not specified
                project = serializer.save(owner_user=request.user)
                
                # Auto-initialize project-specific permissions
                from dms.utils import initialize_project_permissions
                initialize_project_permissions(project)
                
                return JsonResponse({
                    "status": "success",
                    "message": "Project created successfully",
                    "data": serializer.data
                })
            
            print("Validation errors:", serializer.errors)
            
            # Format errors for better readability
            error_messages = []
            for field, errors in serializer.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            return JsonResponse({
                "status": "failed",
                "message": " | ".join(error_messages),
                "errors": serializer.errors,
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f'Exception: {e}')
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "status": "failed",
                "message": str(e),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)


class ProjectUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk, **kwargs):
        try:
            project = Project.objects.get(id=pk)
        except Project.DoesNotExist:
            return JsonResponse({
                "status": "failed",
                "message": "Project not found",
                "data": None
            }, safe=False, status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = ProjectSerializer(project, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Project updated successfully",
                    "data": serializer.data
                })
            return JsonResponse({
                "status": "failed",
                "message": serializer.errors,
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({
                "status": "failed",
                "message": "Something went wrong...",
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, **kwargs):
        try:
            project = Project.objects.get(id=pk)
        except Project.DoesNotExist:
            return JsonResponse({
                "status": "failed",
                "message": "Project not found",
                "data": None
            }, safe=False, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectSerializer(project)
        return JsonResponse({
            "status": "success",
            "message": None,
            "data": serializer.data
        })


class ProjectListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        projects = Project.objects.all()
        
        # Superuser sees all.
        # Others see projects they own OR projects where they have a department role.
        if not request.user.is_superuser:
            projects = projects.filter(
                Q(owner_user=request.user) | 
                Q(team_roles__user=request.user)
            ).distinct()
                
        serializer = ProjectSerializer(projects, many=True)
        return JsonResponse({
            "status": "success",
            "message": None,
            "data": serializer.data
        })


# SubPhase Views
class SubPhaseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        try:
            serializer = SubPhaseSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "status": "success",
                    "message": "SubPhase created successfully",
                    "data": serializer.data
                })
            return JsonResponse({
                "status": "failed",
                "message": serializer.errors,
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({
                "status": "failed",
                "message": "Something went wrong...",
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)


class SubPhaseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        try:
            print (request.query_params)
            project_id = request.query_params.get('project_id')
            subphases = SubPhase.objects.filter(project_id=project_id)
            serializer = SubPhaseSerializer(subphases, many=True)
            return JsonResponse({
                "status": "success",
                "message": None,
                "data": serializer.data
            })
        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({
                "status": "failed",
                "message": "Something went wrong...",
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)


class ProjectHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, **kwargs):
        try:
            project = Project.objects.get(id=pk)
        except Project.DoesNotExist:
            return JsonResponse({"status": "failed", "message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        # 1. Global Task Stats
        from dms.models import Task
        all_project_tasks = Task.objects.filter(project=project)
        total_tasks = all_project_tasks.count()
        completed_tasks = all_project_tasks.filter(status='APPROVED').count()
        overdue_tasks = all_project_tasks.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS'], due_date__lt=request.user.date_joined.today()).count() # Approximation

        # 2. My Task Stats (Personalized)
        my_tasks = all_project_tasks.filter(assigned_to=request.user)
        my_total = my_tasks.count()
        my_completed = my_tasks.filter(status='APPROVED').count()
        my_active = my_tasks.filter(status__in=['ASSIGNED', 'IN_PROGRESS']).count()
        my_overdue = my_tasks.filter(status__in=['ASSIGNED', 'IN_PROGRESS'], due_date__lt=request.user.date_joined.today()).count()

        # 3. Schedule Stats (P6)
        from planning.models import P6Activity
        from django.utils import timezone
        now = timezone.now()
        
        activities = P6Activity.objects.filter(dms_task__project=project)
        total_activities = activities.count()
        delayed_activities = activities.filter(early_finish__lt=now).exclude(status='Completed').count()
        
        schedule_status = "On Track"
        if total_activities > 0:
            delay_ratio = delayed_activities / total_activities
            if delay_ratio > 0.1:
                schedule_status = "Behind Schedule"
            elif delay_ratio < 0:
                schedule_status = "Ahead of Schedule"

        data = {
            "schedule_status": schedule_status,
            # Global
            "tasks_total": total_tasks,
            "tasks_completed": completed_tasks,
            "tasks_overdue": overdue_tasks,
            "activities_total": total_activities,
            "activities_delayed": delayed_activities,
            # Personal
            "my_tasks_total": my_total,
            "my_tasks_completed": my_completed,
            "my_tasks_active": my_active,
            "my_tasks_overdue": my_overdue
        }

        return JsonResponse({
            "status": "success",
            "data": data
        })


class ProjectHealthSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        try:
            projects = Project.objects.all()
            if not request.user.is_superuser:
                projects = projects.filter(
                    Q(owner_user=request.user) | 
                    Q(team_roles__user=request.user)
                ).distinct()

            from dms.models import Task
            from planning.models import P6Activity
            from django.utils import timezone
            now = timezone.now()

            summary_data = {}

            for project in projects:
                # 1. Global Task Stats
                all_project_tasks = Task.objects.filter(project=project)
                total_tasks = all_project_tasks.count()
                completed_tasks = all_project_tasks.filter(status='APPROVED').count()
                tasks_waiting = all_project_tasks.filter(status='ASSIGNED').count()
                tasks_in_progress = all_project_tasks.filter(status='IN_PROGRESS').count()
                
                overdue_tasks = all_project_tasks.filter(
                    status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS'], 
                    due_date__lt=now
                ).count()

                # 2. My Task Stats (Personalized)
                my_tasks = all_project_tasks.filter(assigned_to=request.user)
                my_total = my_tasks.count()
                my_completed = my_tasks.filter(status='APPROVED').count()
                my_waiting = my_tasks.filter(status='ASSIGNED').count()
                my_in_progress = my_tasks.filter(status='IN_PROGRESS').count()
                
                my_overdue = my_tasks.filter(
                    status__in=['ASSIGNED', 'IN_PROGRESS'], 
                    due_date__lt=now
                ).count()

                # 3. Schedule Stats (P6)
                activities = P6Activity.objects.filter(dms_task__project=project)
                total_activities = activities.count()
                delayed_activities = activities.filter(early_finish__lt=now).exclude(status='Completed').count()
                
                schedule_status = "On Track"
                if total_activities > 0:
                    delay_ratio = delayed_activities / total_activities
                    if delay_ratio > 0.1:
                        schedule_status = "Behind Schedule"
                    elif delay_ratio < 0:
                        schedule_status = "Ahead of Schedule"

                summary_data[project.id] = {
                   "project_id": project.id,
                   "project_name": project.name,
                   "schedule_status": schedule_status,
                   "tasks_total": total_tasks,
                   "tasks_completed": completed_tasks,
                   "tasks_waiting": tasks_waiting,
                   "tasks_in_progress": tasks_in_progress,
                   "tasks_overdue": overdue_tasks,
                   "activities_total": total_activities,
                   "activities_delayed": delayed_activities,
                   # Personal
                   "my_tasks_total": my_total,
                   "my_tasks_completed": my_completed,
                   "my_tasks_waiting": my_waiting,
                   "my_tasks_in_progress": my_in_progress,
                   "my_tasks_active": my_waiting + my_in_progress, # Backwards compatibility
                   "my_tasks_overdue": my_overdue
                }

            return JsonResponse({
                "status": "success",
                "data": summary_data
            })
        except Exception as e:
            return JsonResponse({
                "status": "failed",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

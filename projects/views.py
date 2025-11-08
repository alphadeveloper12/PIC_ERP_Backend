from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import Project, SubPhase, Company
from .serializers import ProjectSerializer, SubPhaseSerializer, CompanySerializer


class ProjectCreateView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        try:
            serializer = ProjectSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Project created successfully",
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


class ProjectUpdateView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

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
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

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
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):

        projects = Project.objects.all()

        serializer = ProjectSerializer(projects, many=True)
        return JsonResponse({
            "status": "success",
            "message": None,
            "data": serializer.data
        })


# SubPhase Views
class SubPhaseCreateView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

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
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        try:
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


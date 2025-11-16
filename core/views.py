from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import Company, Profile
from .serializers import CompanySerializer, ProfileSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Department, Role, Permission, RolePermission, UserRole, User
from .serializers import (
    DepartmentSerializer, RoleSerializer, PermissionSerializer,
    UserRoleSerializer, CreateRolePermissionsSerializer, UserMeSerializer
)

# Company Views
class CompanyCreateView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        try:
            serializer = CompanySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Company created successfully",
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


class CompanyListView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        try:
            companies = Company.objects.all()
            serializer = CompanySerializer(companies, many=True)
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


# Profile Views
class ProfileCreateView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        try:
            serializer = ProfileSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Profile created successfully",
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


class ProfileListView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        try:
            profiles = Profile.objects.all()
            serializer = ProfileSerializer(profiles, many=True)
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




# ------------------------
#   DEPARTMENTS
# ------------------------
class DepartmentCreateView(generics.CreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentListView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


# ------------------------
#   ROLES
# ------------------------
class RoleCreateView(generics.CreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class RoleListView(generics.ListAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


# ------------------------
#   PERMISSIONS
# ------------------------
class PermissionCreateView(generics.CreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


class PermissionListView(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


# ------------------------
#   ROLE PERMISSIONS
# ------------------------
class RolePermissionAssignView(generics.GenericAPIView):
    serializer_class = CreateRolePermissionsSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_id = serializer.validated_data["role_id"]
        codes = serializer.validated_data["permission_codes"]

        role = Role.objects.get(id=role_id)

        for code in codes:
            perm = Permission.objects.get(code=code)
            RolePermission.objects.get_or_create(role=role, permission=perm)

        return Response({"message": "Permissions assigned successfully"})


# ------------------------
#   USER DEPARTMENTS + ROLES
# ------------------------
class UserRoleAssignView(generics.CreateAPIView):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer


class UserRolesListView(generics.ListAPIView):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer


# ------------------------
#   /auth/me/
# ------------------------
class MeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

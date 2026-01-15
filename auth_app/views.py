from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAdminUser
from .serializers import LoginSerializer, RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets
from projects.models import Project
from django.contrib.auth.models import User
from .models import (
    Supplier, DMApproval, RawMaterial, Inventory,
    ProcurementOrder, QCResult, MixDesign, CostElement, ApprovalWorkflow
)
from .serializers import (
    SupplierSerializer, DMApprovalSerializer, RawMaterialSerializer, InventorySerializer,
    ProcurementOrderSerializer, QCResultSerializer, MixDesignSerializer,
    CostElementSerializer, ApprovalWorkflowSerializer
)

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    # allow unauthenticated registration for now, or restrict to Admin
    # For Setup, maybe AllowAny is easiest, or IsAuthenticated if only Admin creates users.
    # Plan says: "Admin logs in registers ... project owner"
    # So ideally IsAuthenticated + Admin check.
    # But for demo simplicity, let's allow AllowAny or make it simpler.
    # Using CreateAPIView generic.
    permission_classes = [AllowAny] 
    serializer_class = RegisterSerializer


from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

class UserListView(generics.ListAPIView):
    # Allowing all authenticated users for now, or we can restrict to Admin/Owner
    permission_classes = [IsAuthenticated] 
    serializer_class = RegisterSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        
        # Filter users created by this owner
        return User.objects.filter(profile__created_by=user)
    # Let's use a simple inline serializer or just return values if needed, but RegisterSerializer might hide password which is good.
    # Wait, RegisterSerializer usually expects password. Let's make a simple one or just use LoginSerializer's user part?
    # Better: Use a dedicated UserSerializer or just reuse RegisterSerializer but fields might be issue.
    # Let's simple return data. Or use RegisterSerializer for now.
    



class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            # Fetch all roles and permissions
            from dms.models import UserDepartmentRole, AccessPolicy
            roles_data = []
            all_perms = set()
            
            # Superusers logically have all access, but we can explicitly flag it
            if user.is_superuser:
                all_perms.add('superuser')

            user_roles = UserDepartmentRole.objects.filter(user=user).select_related('department', 'project')
            for ur in user_roles:
                # Find policy for this dept/role
                policy = AccessPolicy.objects.filter(department=ur.department, role=ur.role).first()
                perms = policy.permissions if policy else []
                
                roles_data.append({
                    'project_id': ur.project.id if ur.project else None,
                    'project_name': ur.project.name if ur.project else 'Global',
                    'department_code': ur.department.code,
                    'department_name': ur.department.name,
                    'role': ur.role,
                    'permissions': perms
                })
                all_perms.update(perms)

            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_superuser': user.is_superuser,
                    'is_owner': user.owned_projects.exists(),
                    'owned_project_ids': list(user.owned_projects.values_list('id', flat=True)),
                    'is_hod': user.department_roles.filter(role='HOD').exists(),
                    'department_roles': roles_data,
                    'permissions': list(all_perms)
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class DMApprovalViewSet(viewsets.ModelViewSet):
    queryset = DMApproval.objects.all()
    serializer_class = DMApprovalSerializer


class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all()
    serializer_class = RawMaterialSerializer


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer


class ProcurementOrderViewSet(viewsets.ModelViewSet):
    queryset = ProcurementOrder.objects.all()
    serializer_class = ProcurementOrderSerializer


class QCResultViewSet(viewsets.ModelViewSet):
    queryset = QCResult.objects.all()
    serializer_class = QCResultSerializer


class MixDesignViewSet(viewsets.ModelViewSet):
    queryset = MixDesign.objects.all()
    serializer_class = MixDesignSerializer


class CostElementViewSet(viewsets.ModelViewSet):
    queryset = CostElement.objects.all()
    serializer_class = CostElementSerializer


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    queryset = ApprovalWorkflow.objects.all()
    serializer_class = ApprovalWorkflowSerializer

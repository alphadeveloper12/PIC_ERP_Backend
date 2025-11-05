from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets
from .models import (
    Supplier, DMApproval, RawMaterial, Inventory,
    ProcurementOrder, QCResult, MixDesign, CostElement, ApprovalWorkflow
)
from .serializers import (
    SupplierSerializer, DMApprovalSerializer, RawMaterialSerializer, InventorySerializer,
    ProcurementOrderSerializer, QCResultSerializer, MixDesignSerializer,
    CostElementSerializer, ApprovalWorkflowSerializer
)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
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

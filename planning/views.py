import pandas as pd
from datetime import date
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import P6Activity, MappingResult, PrimaveraSheet
from .serializers import P6ActivitySerializer, PrimaveraSheetSerializer
from .utils import import_primavera_data
from rest_framework import viewsets, status
from dms.permissions import HasRequiredPermission
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from estimation.models import BOQItem
from rl_engine_v2.rl_feedback_v2 import RLFeedbackHandler
from projects.models import SubPhase
import os
import tempfile

class PrimaveraSheetViewSet(viewsets.ModelViewSet):
    queryset = PrimaveraSheet.objects.all()
    serializer_class = PrimaveraSheetSerializer
    permission_classes = [IsAuthenticated, HasRequiredPermission]
    required_permission = 'manage_planning'

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_data(self, request):
        """
        Upload and import Primavera P6 data from Excel.
        Requires 'file' and 'subphase_id'.
        """
        file_obj = request.FILES.get('file')
        subphase_id = request.data.get('subphase_id')
        sheet_name = request.data.get('name', 'Uploaded Sheet')

        if not file_obj or not subphase_id:
            return Response({"error": "file and subphase_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subphase = SubPhase.objects.get(id=subphase_id)
        except SubPhase.DoesNotExist:
            return Response({"error": "SubPhase not found"}, status=status.HTTP_404_NOT_FOUND)

        # Security Check: Ensure user owns this project or is superuser
        if not request.user.is_superuser and subphase.project.owner_user != request.user:
            return Response({"error": "You do not have permission to upload to this project."}, status=status.HTTP_403_FORBIDDEN)

        # Create PrimaveraSheet
        sheet = PrimaveraSheet.objects.create(
            subphase=subphase,
            name=sheet_name,
            file=file_obj
        )

        # Save to temporary file to pass to utility (or use the saved file path)
        # Since we saved it to the model, we can use sheet.file.path
        
        try:
            result = import_primavera_data(sheet.file.path, sheet)
            
            return Response({
                "sheet_id": sheet.id,
                "import_stats": result
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # Cleanup if failed? Maybe keep the sheet record but empty?
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from dms.views import StandardResultsSetPagination

class P6ActivityViewSet(viewsets.ModelViewSet):
    """
    CRUD API for P6Activity.
    Supports filtering by primavera_sheet ID via query param: ?primavera_sheet=1
    """
    queryset = P6Activity.objects.all().order_by('activity_id')
    serializer_class = P6ActivitySerializer
    permission_classes = [IsAuthenticated, HasRequiredPermission]
    required_permission = 'view_planning'
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['primavera_sheet']
    search_fields = ['activity_id', 'activity_name', 'erc_code']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Security: Filter by project ownership
        if not user.is_superuser:
            queryset = queryset.filter(primavera_sheet__subphase__project__owner_user=user)
            
        return queryset


class PrimaveraFeedbackView(APIView):
    """
    API to handle user feedback for BOQ-Primavera linking.
    Payload:
    {
        "boq_item_id": 123,
        "correct_ids": ["A100", "B200"],
        "incorrect_ids": ["C300"]
    }
    """
    def post(self, request):
        boq_item_id = request.data.get('boq_item_id')
        correct_ids = request.data.get('correct_ids', [])
        incorrect_ids = request.data.get('incorrect_ids', [])

        if not boq_item_id:
            return Response({"error": "boq_item_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            boq_item = BOQItem.objects.get(id=boq_item_id)
        except BOQItem.DoesNotExist:
            return Response({"error": "BOQItem not found"}, status=status.HTTP_404_NOT_FOUND)

        handler = RLFeedbackHandler()
        
        # Let's use the full description as the key for negative links
        # Ideally this should match the context used in linking
        combined_context = boq_item.description.strip() 
        
        # 1. Handle Incorrect IDs (Negative Feedback)
        for bad_id in incorrect_ids:
            handler.update_primavera_negative_link(combined_context, bad_id)

        # 2. Handle Correct IDs (Positive Feedback & DB Saving)
        saved_count = 0
        for good_id in correct_ids:
            # Save to JSON for immediate override in linking script
            handler.update_primavera_link(combined_context, good_id)
            
            # Save to MappingResult
            try:
                p6_activity = P6Activity.objects.get(activity_id=good_id)
                MappingResult.objects.update_or_create(
                    boq=boq_item,
                    p6=p6_activity,
                    defaults={'confidence': 1.0} # Manual feedback implies 100% confidence
                )
                saved_count += 1
            except P6Activity.DoesNotExist:
                print(f"Warning: P6Activity {good_id} not found in DB.")

        return Response({
            "message": "Feedback applied successfully",
            "saved_mappings": saved_count,
            "negative_feedback_applied": len(incorrect_ids)
        }, status=status.HTTP_200_OK)

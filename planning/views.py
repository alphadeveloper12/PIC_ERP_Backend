from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Planning, XerImportJob
from .serializers import XerImportSerializer
from .tasks import import_xer_background  # ✅ one-way import only

class XerImportAPIView(APIView):
    def post(self, request, planning_id):
        serializer = XerImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        xer_file = serializer.validated_data["xer_file"]

        try:
            planning = Planning.objects.get(id=planning_id)
        except Planning.DoesNotExist:
            return Response({"error": "Planning not found"}, status=404)

        job = XerImportJob.objects.create(planning=planning, file=xer_file)
        import_xer_background.delay(job.id)

        return Response({
            "message": "⏳ Import started",
            "job_id": job.id,
            "status_endpoint": f"/api/xer-imports/{job.id}/status/"
        }, status=202)

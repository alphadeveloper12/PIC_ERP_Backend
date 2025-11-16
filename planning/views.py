import pandas as pd
from datetime import date
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Project, Category, SubCategory, Activity
from .serializers import ProjectSerializer


class UploadPrimaveraView(APIView):
    """
    Upload an Excel file and automatically parse and save hierarchy
    (Project → Category → Subcategory → Activities)
    """

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read Excel file
            df = pd.read_excel(file)
            df["Activity Location"] = ""

            # Function to detect hierarchy level by indentation
            def get_indent_level(val):
                if pd.isna(val):
                    return None
                spaces = len(val) - len(val.lstrip(' '))
                if spaces == 0:
                    return 0
                elif spaces == 2:
                    return 1
                elif spaces == 4:
                    return 2
                else:
                    return 3

            df["Level"] = df["Activity ID"].apply(get_indent_level)

            # Safe date conversion helper
            def safe_date(val):
                if pd.isna(val):
                    return None
                if isinstance(val, pd.Timestamp):
                    return val.date()
                if isinstance(val, date):
                    return val
                return None

            # Initialize placeholders
            project = None
            category = None
            subcategory = None
            activities_to_create = []

            with transaction.atomic():  # ensure atomic insert
                for _, row in df.iterrows():
                    level = row["Level"]

                    if level == 0:
                        project, _ = Project.objects.get_or_create(name=row["Activity ID"].strip())

                    elif level == 1 and project:
                        category, _ = Category.objects.get_or_create(
                            project=project,
                            name=row["Activity ID"].strip()
                        )

                    elif level == 2 and category:
                        subcategory, _ = SubCategory.objects.get_or_create(
                            category=category,
                            name=row["Activity ID"].strip()
                        )

                    elif level == 3 and subcategory:
                        activity = Activity(
                            subcategory=subcategory,
                            activity_id=row["Activity ID"].strip(),
                            activity_name=row.get("Activity Name"),
                            original_duration=row.get("Original Duration"),
                            early_start=safe_date(row.get("Early Start")),
                            early_finish=safe_date(row.get("Early Finish")),
                            late_start=safe_date(row.get("Late Start")),
                            late_finish=safe_date(row.get("Late Finish")),
                            total_float=row.get("Total Float"),
                            budgeted_total_cost=row.get("Budgeted Total Cost"),
                            owner=row.get("Owner"),
                            activity_location=row.get("Activity Location", "")
                        )
                        activities_to_create.append(activity)

                # Bulk insert all activities at once
                if activities_to_create:
                    Activity.objects.bulk_create(activities_to_create, batch_size=1000)

            return Response(
                {"message": f"✅ Data imported successfully — {len(activities_to_create)} activities saved."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": f"Import failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectHierarchyView(generics.ListAPIView):
    """
    Retrieve full Primavera hierarchy (Project → Category → Subcategory → Activities)
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
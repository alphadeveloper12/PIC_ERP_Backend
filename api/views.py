# # api/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from projects.models import Project
# from .serializers import *
# from django.db import transaction
# import pandas as pd
#
#
# class ProjectView(APIView):
#     def get(self, request):
#         # Fetch all projects
#         projects = Project.objects.all()
#         serializer = ProjectSerializer(projects, many=True)
#         return Response(serializer.data)
#
#     def post(self, request):
#         # Create a new project
#         serializer = ProjectSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ProjectDetailView(APIView):
#     def get(self, request, project_id):
#         # Fetch a single project by ID
#         try:
#             project = Project.objects.get(id=project_id)
#         except Project.DoesNotExist:
#             return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = ProjectSerializer(project)
#         return Response(serializer.data)
#
#     def put(self, request, project_id):
#         # Update a project by ID
#         try:
#             project = Project.objects.get(id=project_id)
#         except Project.DoesNotExist:
#             return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = ProjectSerializer(project, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ProjectPhaseView(APIView):
#     def get(self, request, project_id):
#         # Fetch all phases for a project
#         try:
#             project = Project.objects.get(id=project_id)
#         except Project.DoesNotExist:
#             return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         phases = ProjectPhase.objects.filter(project=project)
#         serializer = ProjectPhaseSerializer(phases, many=True)
#         return Response(serializer.data)
#
#     def post(self, request, project_id):
#         # Create a new phase for the project
#         try:
#             project = Project.objects.get(id=project_id)
#         except Project.DoesNotExist:
#             return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = ProjectPhaseSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(project=project)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ProjectPhaseDetailView(APIView):
#     def get(self, request, phase_id):
#         # Fetch a single phase by ID
#         try:
#             phase = ProjectPhase.objects.get(id=phase_id)
#         except ProjectPhase.DoesNotExist:
#             return Response({"error": "Phase not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = ProjectPhaseSerializer(phase)
#         return Response(serializer.data)
#
#     def put(self, request, phase_id):
#         # Update a project phase
#         try:
#             phase = ProjectPhase.objects.get(id=phase_id)
#         except ProjectPhase.DoesNotExist:
#             return Response({"error": "Phase not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = ProjectPhaseSerializer(phase, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# class BoqView(APIView):
#     def get(self, request, project_id):
#         # Fetch all BoQs for the project
#         try:
#             project = Project.objects.get(id=project_id)
#         except Project.DoesNotExist:
#             return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         estimations = Estimation.objects.filter(project=project)
#         boqs = Boq.objects.filter(estimation__in=estimations)
#         serializer = BoqSerializer(boqs, many=True)
#         return Response(serializer.data)
#
#     def post(self, request, project_id):
#         # Create a new BoQ for the project
#         try:
#             project = Project.objects.get(id=project_id)
#         except Project.DoesNotExist:
#             return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         estimation = Estimation.objects.filter(project=project).order_by('-revision_no').first()
#         if not estimation:
#             return Response({"error": "No estimation found for the project"}, status=status.HTTP_400_BAD_REQUEST)
#
#         serializer = BoqSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(estimation=estimation)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class BoqDetailView(APIView):
#     def get(self, request, boq_id):
#         # Fetch a single BoQ by ID
#         try:
#             boq = Boq.objects.get(id=boq_id)
#         except Boq.DoesNotExist:
#             return Response({"error": "BoQ not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = BoqSerializer(boq)
#         return Response(serializer.data)
#
#     def put(self, request, boq_id):
#         # Update a BoQ by ID
#         try:
#             boq = Boq.objects.get(id=boq_id)
#         except Boq.DoesNotExist:
#             return Response({"error": "BoQ not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = BoqSerializer(boq, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# import pandas as pd
# from django.db import transaction
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from estimation.models import Boq, BoqSection, BoqItem, Estimation
# from projects.models import Project
# from core.models import Company
#
#
# # ===== Config =====
# REQUIRED_COLS = {
#     "item_no", "description", "unit", "quantity", "rate",
#     "material_rate", "material_wastage", "plant_rate",
#     "labour_hours", "subcontract_rate",
#     "others_1_qty", "others_1_rate", "others_2_qty", "others_2_rate",
#     "dry_cost", "unit_rate", "prelimin", "boq_amount",
#     "actual_qty", "actual_amount", "factor", "material"
# }
#
# ALIASES = {
#     "labour_hrs": "labour_hours",
#     "labor_hours": "labour_hours",
#     "u_rate": "unit_rate",
#     "prelim": "prelimin",
#     "boq": "boq_amount",
#     "materials": "material",
#     "plant": "plant_rate",
#     "description_of_work": "description",
#     "desc": "description",
# }
#
# BULK_SIZE = 1000
# HEADER_ROWS_TO_TRY = 3         # try first 3 rows as header
# SAMPLE_ROWS_PER_SHEET = 10     # sample a few rows per sheet to score
# REPLACE_MATERIALS = True       # True: delete + re-insert per item on each upload
# # =================================================
#
#
# class BoqExcelUploadView(APIView):
#     def post(self, request, project_id):
#         # Ensure the file is provided in the request
#         if "file" not in request.FILES:
#             return Response({"error": "Excel file is required"}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Try to fetch the project
#         try:
#             project = Project.objects.get(id=project_id)
#         except Project.DoesNotExist:
#             return Response({"error": "Invalid project ID"}, status=status.HTTP_404_NOT_FOUND)
#
#         # Read the excel file into a DataFrame
#         fobj = request.FILES["file"]
#         df = pd.read_excel(fobj, dtype=str)
#
#         # ===== Clean up column names by removing newline characters and extra spaces =====
#         df.columns = df.columns.str.replace(r'\n', '', regex=True).str.strip().str.lower().str.replace(" ", "_")
#
#         # Debugging: Log the columns to check if 'item_no' exists after cleaning
#         print("Cleaned Columns:", df.columns)
#
#         # Check if 'item_no' exists
#         if "item_no" not in df.columns:
#             return Response({"error": "The column 'item_no' is missing from the uploaded file."}, status=status.HTTP_400_BAD_REQUEST)
#
#         # ===== Alias the columns according to the ALIASES =====
#         df = df.rename(columns={col: ALIASES.get(col, col) for col in df.columns})
#
#         # ===== Filter out rows where 'item_no' is NaN, likely section headers =====
#         df = df.dropna(subset=["item_no"])
#
#         # ===== Coerce 'quantity' and 'rate' to numeric and fill NaN with 0 =====
#         df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
#         df["rate"] = pd.to_numeric(df["rate"], errors="coerce").fillna(0)
#
#         # ===== Remove rows where both 'quantity' and 'rate' are zero =====
#         df = df[(df["quantity"] > 0) | (df["rate"] > 0)]
#
#         # ===== Normalize description and mark rows that are sections =====
#         df["description"] = df["description"].fillna("").astype(str)
#         df["is_section"] = df["description"].str.upper().str.startswith("SECTION")
#         df["section_name"] = df["description"].where(df["is_section"]).ffill()
#
#         # ===== Get the latest estimation for the project, or create a default one if not found =====
#         estimation = Estimation.objects.filter(project=project).order_by("-revision_no").first()
#         if not estimation:
#             estimation = Estimation.objects.create(company=project.company, project=project, name="Initial Estimation")
#
#         # ===== Create the main BoQ object =====
#         boq = Boq.objects.create(estimation=estimation, title="Imported BOQ")
#
#         # ===== Process each section and its items in the DataFrame =====
#         with transaction.atomic():
#             for section_name, group in df.groupby("section_name"):
#                 # Create a BoQ section for each section in the Excel file
#                 section = BoqSection.objects.create(boq=boq, title=section_name)
#
#                 # Iterate through each row in the section and create BoQ items
#                 for _, row in group.iterrows():
#                     if row["is_section"]:
#                         continue  # Skip section rows
#
#                     # Coerce numerics and calculate amount
#                     quantity = float(row["quantity"])
#                     rate = float(row["rate"])
#                     amount = quantity * rate
#
#                     # Create a BoQ item for each row in the section
#                     BoqItem.objects.create(
#                         section=section,
#                         item_no=row.get("item_no", ""),
#                         description=row.get("description", ""),
#                         unit=row.get("unit", ""),
#                         quantity=quantity,
#                         rate=rate,
#                         amount=amount,
#                     )
#
#         return Response({"message": "BOQ uploaded successfully", "boq_id": boq.id}, status=status.HTTP_201_CREATED)
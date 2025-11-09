from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError
from .functions import calculate_file_hash, extract_boq
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

from .serializers import *
import json

from collections import defaultdict
from django.db.models import Q, Sum, Prefetch
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from django.db import transaction
from django.http import HttpResponse
import io

from estimation.models import BOQItem, Subsection, Section
from .serializers import BOQItemSerializer
from excel.serializers import AppConfigKV, AppConfigSerializer
from excel.permissions import RolePermission
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from collections import defaultdict
from django.http import HttpResponse
from rest_framework.views import APIView
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io



# Estimation Views
class EstimationCreateView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        try:
            serializer = EstimationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Estimation created successfully",
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


class EstimationUpdateView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def put(self, request, pk, **kwargs):
        try:
            estimation = Estimation.objects.get(id=pk)
        except Estimation.DoesNotExist:
            return JsonResponse({
                "status": "failed",
                "message": "Estimation not found",
                "data": None
            }, safe=False, status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = EstimationSerializer(estimation, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Estimation updated successfully",
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


class EstimationListView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        try:
            project_id = request.query_params.get('project_id')
            estimations = Estimation.objects.filter(subphase__project_id=project_id)
            serializer = EstimationSerializer(estimations, many=True)
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


class UploadBOQ(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Extract the file and estimation_id from the request
        file = request.FILES.get('boq_file')
        estimation_id = request.data.get('estimation_id')

        if not file:
            return Response({'detail': 'BOQ file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not estimation_id:
            return Response({'detail': 'Estimation ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Extract the Estimation object
            estimation = Estimation.objects.get(id=estimation_id)
        except Estimation.DoesNotExist:
            return Response({'detail': 'Estimation not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Process the BOQ file
        try:
            file_hash = calculate_file_hash(file)
            # Check for existing BOQ with the same file hash for the given estimation
            existing_boq = BOQ.objects.filter(estimation=estimation, file_hash=file_hash).first()
            if existing_boq:
                return Response({'detail': 'Duplicate BOQ file found, skipping extraction.'}, status=status.HTTP_200_OK)

            # Proceed with BOQ data extraction
            boq = BOQ.objects.create(
                name=f"BOQ for {estimation.subphase.name}",
                estimation=estimation,
                file_path=file,
                file_hash=file_hash
            )
            print(boq)
            print(file)
            resp = extract_boq(file, boq)
            if resp:
                return Response({'detail': 'BOQ data extracted and saved successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'detail': 'DID NOT EXTRACT'}, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BOQListView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        try:
            project_id = request.query_params.get('project_id')
            boqs = BOQ.objects.filter(estimation__subphase__project_id=project_id)
            data = BOQSerializer(boqs, many=True).data

            return JsonResponse({
                "status": "success",
                "message": None,
                "data": data
            })
        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({
                "status": "failed",
                "message": "Something went wrong...",
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)


class BOQDetailView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk, **kwargs):
        try:
            # Fetch the specific BOQ by ID
            boq = BOQ.objects.get(id=pk)

            # Serialize the data for BOQ, Sections, Subsections, and BOQItems
            boq_serializer = BOQDetailSerializer(boq)
            # sections = Section.objects.filter(boq=boq)
            # subsections = Subsection.objects.filter(section__in=sections)
            # boq_items = BOQItem.objects.filter(subsection__in=subsections)

            # sections_serializer = SectionSerializer(sections, many=True)
            # subsections_serializer = SubsectionSerializer(subsections, many=True)
            # boq_items_serializer = BOQItemSerializer(boq_items, many=True)

            return JsonResponse({
                "status": "success",
                "message": None,
                "data": boq_serializer.data,
            })
        except BOQ.DoesNotExist:
            return JsonResponse({
                "status": "failed",
                "message": "BOQ not found",
                "data": None
            }, safe=False, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({
                "status": "failed",
                "message": "Something went wrong...",
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)


class BOQUpdateView(APIView):
    def put(self, request, pk, **kwargs):
        try:
            # Fetch the specific BOQ by ID
            boq = BOQ.objects.get(id=pk)

            # Save the current values for revision logging
            original_boq = BOQSerializer(boq)
            original_sections = Section.objects.filter(boq=boq)
            original_subsections = Subsection.objects.filter(section__in=original_sections)
            original_boq_items = BOQItem.objects.filter(subsection__in=original_subsections)

            # Create a list of changes that will be logged in the BOQRevision table
            revisions = []
            revision_fields = {}

            # Update the BOQ itself (name or other fields)
            if 'name' in request.data:
                new_name = request.data['name']
                if boq.name != new_name:
                    revision_fields["name"] = {
                        "old_value": boq.name,
                        "new_value": new_name
                    }
                    boq.name = new_name  # Update the BOQ name
                    boq.save()  # Save the updated BOQ

            # Iterate through the sections and check for changes
            if 'sections' in request.data:
                section_data = request.data['sections']
                for data in section_data:
                    section = Section.objects.get(id=data['id'])
                    if section.name != data['name']:
                        revision_fields["section"] = {
                            "old_value": section.name,
                            "new_value": data['name']
                        }
                        section.name = data['name']
                        section.save()

            # Iterate through the subsections and check for changes
            if 'subsections' in request.data:
                subsection_data = request.data['subsections']
                for data in subsection_data:
                    subsection = Subsection.objects.get(id=data['id'])
                    if subsection.name != data['name']:
                        revision_fields["subsection"] = {
                            "old_value": subsection.name,
                            "new_value": data['name']
                        }
                        subsection.name = data['name']
                        subsection.save()

            # Iterate through the BOQItems and check for changes
            if 'boq_items' in request.data:
                boq_item_data = request.data['boq_items']
                for boq_item in original_boq_items:
                    for data in boq_item_data:
                        if data.get('id') == boq_item.id:
                            # Prepare the old values and new values for BOQItem fields
                            old_boq_item = {
                                "description": boq_item.description,
                                "unit": boq_item.unit,
                                "quantity": str(boq_item.quantity),  # Ensure it's a string
                                "rate": str(boq_item.rate),
                                "amount": str(boq_item.amount),
                                "subsection_id": boq_item.subsection.id  # Save only the ID of Subsection
                            }
                            new_boq_item = {
                                "description": data.get('description'),
                                "unit": data.get('unit'),
                                "quantity": str(data.get('quantity', 0)),
                                "rate": str(data.get('rate', 0)),
                                "amount": str(data.get('amount', 0)),
                                "subsection_id": data.get('subsection', boq_item.subsection.id)  # Save only the ID of Subsection
                            }

                            # If any fields have changed, log the change as a single revision entry
                            if old_boq_item != new_boq_item:
                                # Log the old and new values for BOQItem
                                revision_fields["boq_item"] = {
                                    "old_value": old_boq_item,
                                    "new_value": new_boq_item
                                }

                            # Update the BOQItem
                            boq_item.description = data.get('description')
                            boq_item.unit = data.get('unit')
                            boq_item.quantity = data.get('quantity')
                            boq_item.rate = data.get('rate')
                            boq_item.amount = data.get('amount')

                            # Update the related foreign key for the subsection if it changed
                            if data.get('subsection') != boq_item.subsection.id:
                                boq_item.subsection = Subsection.objects.get(id=data.get('subsection'))

                            boq_item.save()

            # Now log the changes in a single BOQRevision entry
            if revision_fields:
                revision_data = {
                    "boq": boq,
                    "old_value": json.dumps(revision_fields),
                    "new_value": json.dumps(revision_fields),
                    "updated_at": timezone.now()
                }
                BOQRevision.objects.create(**revision_data)

            return JsonResponse({
                "status": "success",
                "message": "BOQItem(s), Section(s), Subsection(s) updated successfully",
                "data": "Updated BOQItems, Sections, and Subsections successfully"
            })
        except BOQ.DoesNotExist:
            return JsonResponse({
                "status": "failed",
                "message": "BOQ not found",
                "data": None
            }, safe=False, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({
                "status": "failed",
                "message": "Something went wrong...",
                "data": None
            }, safe=False, status=status.HTTP_400_BAD_REQUEST)


# ---------- Grouped + Subtotals + GrandTotal (+addons) ----------
class BOQGroupedView(APIView):
    """
    Groups BOQ items by Section and calculates subtotals and grand totals,
    including tax and overheads.
    """
    def get(self, request):
        # fetch non-deleted items with optimized joins
        items = (
            BOQItem.objects
            .filter(is_deleted=False)
            .select_related("subsection__section")
        )

        cfg, _ = AppConfigKV.objects.get_or_create(pk=1)

        # skip unwanted descriptions (case-insensitive)
        unwanted = ["collection", "total brought forward from page no.", "carried to final summary"]
        q_unwanted = Q()
        for u in unwanted:
            q_unwanted |= Q(description__iexact=u)
        items = items.exclude(q_unwanted)

        # group by section
        grouped = defaultdict(list)
        for it in items:
            section_name = (
                it.subsection.section.name
                if it.subsection and it.subsection.section
                else "Uncategorized"
            )
            grouped[section_name].append(it)

        sections = []
        grand = 0.0
        for sec_name, rows in grouped.items():
            # derive section_factor from first item or default 0
            section_factor = rows[0].factor if rows else 0.0

            serialized = BOQItemSerializer(rows, many=True).data

            subtotal = sum(float(r.get("amount") or 0) for r in serialized)
            subtotal_with_factor = subtotal * (1 + (section_factor or 0.0) / 100)
            grand += subtotal_with_factor

            sections.append({
                "name": sec_name,
                "subtotal": subtotal_with_factor,
                "section_factor": section_factor,
                "items": serialized
            })

        tax = grand * (cfg.tax_rate or 0)
        overhead = grand * (cfg.overhead_rate or 0)
        grand_total = grand + tax + overhead

        return Response({
            "sections": sections,
            "baseTotal": grand,
            "tax": tax,
            "overhead": overhead,
            "grandTotal": grand_total,
            "config": AppConfigSerializer(cfg).data
        })


# ---------- Update one item (inline) ----------
class BOQItemUpdateView(generics.RetrieveUpdateAPIView):
    queryset = BOQItem.objects.all()
    serializer_class = BOQItemSerializer
    permission_classes = [RolePermission]


# ---------- Create/Delete/Restore/Hard-delete ----------
class BOQItemCreateView(generics.CreateAPIView):
    serializer_class = BOQItemSerializer
    permission_classes = [RolePermission]


class BOQItemSoftDeleteView(APIView):
    def delete(self, request, pk):
        try:
            item = BOQItem.objects.get(pk=pk)
            item.soft_delete(reason=request.query_params.get("reason", ""))
            return Response(status=204)
        except BOQItem.DoesNotExist:
            return Response(status=404)


class BOQItemRestoreView(APIView):
    def post(self, request, pk):
        try:
            item = BOQItem.objects.get(pk=pk)
            item.restore()
            return Response(status=200)
        except BOQItem.DoesNotExist:
            return Response(status=404)


class BOQItemHardDeleteView(generics.DestroyAPIView):
    queryset = BOQItem.objects.all()
    permission_classes = [RolePermission]


# ---------- Reorder inside a subsection ----------
class ReorderView(APIView):
    """
    Payload: { "subsection_id": 12, "ids": [5,3,9,...] }
    """
    def post(self, request):
        subsection_id = request.data.get("subsection_id")
        ids = request.data.get("ids", [])
        if not subsection_id or not isinstance(ids, list):
            return Response({"detail": "Invalid payload"}, status=400)

        with transaction.atomic():
            for idx, _id in enumerate(ids, start=1):
                BOQItem.objects.filter(pk=_id, subsection_id=subsection_id).update(sort_order=idx)
        return Response({"message": "Reordered"}, status=200)


class ExportExcelView(APIView):
    """
    Exports BOQ hierarchy (Section → Subsection → Items) to Excel
    with indentation and subtotal layout like a professional BOQ sheet.
    """

    def get(self, request, boq_id):
        # 1️⃣ Get the BOQ
        try:
            boq = BOQ.objects.get(pk=boq_id)
        except BOQ.DoesNotExist:
            return Response({"detail": "BOQ not found"}, status=404)

        # 2️⃣ Prefetch related data
        item_qs = BOQItem.objects.filter(is_deleted=False).order_by("sort_order", "id")
        subsection_qs = Subsection.objects.prefetch_related(
            Prefetch("items", queryset=item_qs, to_attr="prefetched_items")
        )
        sections = (
            Section.objects
            .filter(boq=boq)
            .order_by("id")
            .prefetch_related(
                Prefetch("subsections", queryset=subsection_qs, to_attr="prefetched_subsections")
            )
        )

        cfg, _ = AppConfigKV.objects.get_or_create(pk=1)

        # 3️⃣ Workbook setup
        wb = Workbook()
        ws = wb.active
        ws.title = "BOQ Export"

        # ---- Branding Header ----
        ws.merge_cells("A1:G1")
        ws["A1"] = cfg.brand_title or f"Bill of Quantities - {boq.name}"
        ws["A1"].font = Font(size=14, bold=True)
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A2:G2")
        subtitle = cfg.brand_subtitle or (boq.estimation.subphase.project.name if boq.estimation else "")
        ws["A2"] = subtitle
        ws["A2"].alignment = Alignment(horizontal="center")

        # ---- Column Headers ----
        headers = ["Item No", "Description", "Unit", "Quantity", "Rate", "Amount"]
        ws.append([])
        ws.append(headers)
        for c in range(1, len(headers) + 1):
            ws.cell(row=3, column=c).font = Font(bold=True)
            ws.cell(row=3, column=c).alignment = Alignment(horizontal="center", vertical="center")

        thin = Side(border_style="thin", color="999999")
        row_idx = 4
        base_total = 0.0

        # 4️⃣ Hierarchical Writing
        for section in sections:
            # Section Header Row
            ws.append([None, f"SECTION - {section.name}"])
            ws.cell(row=row_idx, column=2).font = Font(bold=True, size=11)
            row_idx += 1

            for subsection in getattr(section, "prefetched_subsections", []):
                # Subsection Header
                ws.append(["", f"{subsection.name}"])
                ws.cell(row=row_idx, column=2).font = Font(italic=True)
                row_idx += 1

                items = getattr(subsection, "prefetched_items", [])
                if not items:
                    continue

                for item in items:
                    # Indented BOQ Item
                    ws.append([
                        item.id,  # or item code (if you add one later)
                        f"   {item.description or ''}",
                        item.unit or "",
                        float(item.quantity or 0),
                        float(item.rate or 0),
                        float(item.amount or 0)
                    ])
                    for c in range(1, 7):
                        ws.cell(row=row_idx, column=c).border = Border(top=thin, bottom=thin, left=thin, right=thin)
                    base_total += float(item.amount or 0)
                    row_idx += 1

                # Small gap between subsections
                ws.append([])
                row_idx += 1

            # Section subtotal
            ws.append(["", f"Carried to Collection", "", "", "", "AED"])
            for c in range(1, 7):
                ws.cell(row=row_idx, column=c).font = Font(bold=True)
                ws.cell(row=row_idx, column=c).fill = PatternFill("solid", fgColor="FFF4D7")
            row_idx += 2

        # 5️⃣ Totals
        tax = base_total * (cfg.tax_rate or 0)
        overhead = base_total * (cfg.overhead_rate or 0)
        grand = base_total + tax + overhead

        ws.append([])
        row_idx += 1
        totals = [
            ("Base Total:", base_total),
            (f"Tax ({(cfg.tax_rate or 0)*100:.1f}%)", tax),
            (f"Overhead ({(cfg.overhead_rate or 0)*100:.1f}%)", overhead),
            ("Grand Total:", grand),
        ]
        for label, value in totals:
            ws.append(["", "", "", "", label, value])
            for c in range(1, 7):
                ws.cell(row=row_idx, column=c).font = Font(bold=True)
            row_idx += 1

        # Highlight Grand Total
        for c in range(1, 7):
            ws.cell(row=row_idx - 1, column=c).fill = PatternFill("solid", fgColor="E2F0D9")

        # 6️⃣ Safe autosizing
        for i, column_cells in enumerate(ws.iter_cols(min_row=3, max_row=row_idx), start=1):
            column_letter = get_column_letter(i)
            max_len = 12
            for cell in column_cells:
                if cell.value:
                    try:
                        max_len = max(max_len, len(str(cell.value)))
                    except Exception:
                        pass
            ws.column_dimensions[column_letter].width = min(max_len + 2, 60)

        # 7️⃣ Return Excel
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = HttpResponse(
            buf.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        resp['Content-Disposition'] = f'attachment; filename=BOQ_{boq_id}_Hierarchical.xlsx'
        return resp


class ExportPDFView(APIView):
    """
    Export a single BOQ (by id) to a PDF table with wrapped text.
    Columns: Section, Subsection, Description, Unit, Quantity, Rate, Amount.
    """
    def get(self, request, boq_id):
        # 1) Get BOQ
        try:
            boq = BOQ.objects.get(pk=boq_id)
        except BOQ.DoesNotExist:
            return Response({"detail": "BOQ not found"}, status=404)

        # 2) Prefetch related data
        item_qs = BOQItem.objects.filter(is_deleted=False).order_by("sort_order", "id")
        subsection_qs = Subsection.objects.prefetch_related(
            Prefetch("items", queryset=item_qs, to_attr="prefetched_items")
        )
        sections = (
            Section.objects
            .filter(boq=boq)
            .order_by("id")
            .prefetch_related(
                Prefetch("subsections", queryset=subsection_qs, to_attr="prefetched_subsections")
            )
        )

        cfg, _ = AppConfigKV.objects.get_or_create(pk=1)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(A4),
            leftMargin=24, rightMargin=24,
            topMargin=24, bottomMargin=24
        )
        story = []
        styles = getSampleStyleSheet()

        # Add custom wrapping styles
        wrap_normal = ParagraphStyle(
            "wrap_normal",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            spaceAfter=2,
            wordWrap='CJK',   # enables wrapping even without spaces
        )
        wrap_bold = ParagraphStyle(
            "wrap_bold",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            spaceAfter=2,
            wordWrap='CJK',
            fontName="Helvetica-Bold"
        )

        # ----- Header -----
        header_flow = []
        if cfg.logo_url:
            try:
                header_flow.append(RLImage(cfg.logo_url, width=80, height=80))
            except Exception:
                pass

        title_text = cfg.brand_title or f"Bill of Quantities - {boq.name}"
        header_flow.append(Paragraph(f"<b>{title_text}</b>", styles['Title']))

        subtitle = cfg.brand_subtitle or (boq.estimation.subphase.project.name if boq.estimation else "")
        if subtitle:
            header_flow.append(Paragraph(subtitle, styles['Normal']))

        story += header_flow + [Spacer(1, 12)]

        # ----- Table -----
        data = [["Section", "Subsection", "Description", "Unit", "Quantity", "Rate", "Amount"]]
        base_total = 0.0

        for section in sections:
            section_name = section.name
            subsections = getattr(section, "prefetched_subsections", section.subsections.all())

            for subsection in subsections:
                subsection_name = subsection.name
                items = getattr(subsection, "prefetched_items", subsection.items.filter(is_deleted=False))

                for item in items:
                    qty = float(item.quantity or 0)
                    rate = float(item.rate or 0)
                    amount = float(item.amount or 0)
                    base_total += amount

                    data.append([
                        Paragraph(section_name, wrap_normal),
                        Paragraph(subsection_name, wrap_normal),
                        Paragraph(item.description or "", wrap_normal),
                        Paragraph(item.unit or "", wrap_normal),
                        Paragraph(f"{qty:g}", wrap_normal),
                        Paragraph(f"{rate:g}", wrap_normal),
                        Paragraph(f"{amount:g}", wrap_normal),
                    ])

        tbl = Table(
            data,
            repeatRows=1,
            colWidths=[100, 120, 250, 50, 60, 60, 80]
        )
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Ensures wrapped text starts from top
        ]))
        story += [tbl, Spacer(1, 12)]

        # ----- Totals -----
        tax = base_total * (cfg.tax_rate or 0)
        overhead = base_total * (cfg.overhead_rate or 0)
        grand = base_total + tax + overhead

        totals = [
            ["Base Total", f"{base_total:g}"],
            [f"Tax ({(cfg.tax_rate or 0)*100:.1f}%)", f"{tax:g}"],
            [f"Overhead ({(cfg.overhead_rate or 0)*100:.1f}%)", f"{overhead:g}"],
            ["Grand Total", f"{grand:g}"],
        ]
        t = Table(totals, colWidths=[200, 120])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2F0D9")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story += [Spacer(1, 8), t]

        # ----- Build PDF -----
        doc.build(story)
        buf.seek(0)

        resp = HttpResponse(buf.read(), content_type="application/pdf")
        resp['Content-Disposition'] = f'attachment; filename=BOQ_{boq_id}_Report.pdf'
        return resp



# ---------- MATERIAL ----------
class MaterialCreateView(generics.CreateAPIView):
    serializer_class = MaterialSerializer
    queryset = Material.objects.all()


class MaterialUpdateView(generics.UpdateAPIView):
    serializer_class = MaterialSerializer
    queryset = Material.objects.all()
    lookup_field = "pk"


class MaterialByBOQItemView(APIView):
    def get(self, request, boq_item_id):
        materials = Material.objects.filter(boq_item_id=boq_item_id)
        serializer = MaterialSerializer(materials, many=True)
        return Response(serializer.data)


# ---------- PLANT ----------
class PlantCreateView(generics.CreateAPIView):
    serializer_class = PlantSerializer
    queryset = Plant.objects.all()


class PlantUpdateView(generics.UpdateAPIView):
    serializer_class = PlantSerializer
    queryset = Plant.objects.all()
    lookup_field = "pk"


class PlantByBOQItemView(APIView):
    def get(self, request, boq_item_id):
        plants = Plant.objects.filter(boq_item_id=boq_item_id)
        serializer = PlantSerializer(plants, many=True)
        return Response(serializer.data)


# ---------- LABOUR ----------
class LabourCreateView(generics.CreateAPIView):
    serializer_class = LabourSerializer
    queryset = Labour.objects.all()


class LabourUpdateView(generics.UpdateAPIView):
    serializer_class = LabourSerializer
    queryset = Labour.objects.all()
    lookup_field = "pk"


class LabourByBOQItemView(APIView):
    def get(self, request, boq_item_id):
        labours = Labour.objects.filter(boq_item_id=boq_item_id)
        serializer = LabourSerializer(labours, many=True)
        return Response(serializer.data)


# ---------- SUBCONTRACT ----------
class SubcontractCreateView(generics.CreateAPIView):
    serializer_class = SubcontractSerializer
    queryset = Subcontract.objects.all()


class SubcontractUpdateView(generics.UpdateAPIView):
    serializer_class = SubcontractSerializer
    queryset = Subcontract.objects.all()
    lookup_field = "pk"


class SubcontractByBOQItemView(APIView):
    def get(self, request, boq_item_id):
        subs = Subcontract.objects.filter(boq_item_id=boq_item_id)
        serializer = SubcontractSerializer(subs, many=True)
        return Response(serializer.data)
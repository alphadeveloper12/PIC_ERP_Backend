from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError
from .functions import calculate_file_hash, extract_boq
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import Estimation, BOQ, BOQItem, Section, Subsection, BOQRevision, timezone
from .serializers import EstimationSerializer, BOQSerializer, SectionSerializer, \
    SubsectionSerializer, BOQItemSerializer, BOQDetailSerializer
import json


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
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import Company, Profile
from .serializers import CompanySerializer, ProfileSerializer


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


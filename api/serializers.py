# # api/serializers.py
# from rest_framework import serializers
# from projects.models import Project, ProjectPhase
# from estimation.models import Estimation, Boq, BoqSection, BoqItem
#
#
#
# class ProjectSerializer(serializers.ModelSerializer):
#     code = serializers.CharField(required=False)
#     class Meta:
#         model = Project
#         fields = "__all__"  # Include all fields
#
#     def create(self, validated_data):
#         # The code will be generated in the signal before saving
#         project = Project(**validated_data)  # Do not pass 'code' field explicitly
#         project.save()
#         return project
#
#
# class ProjectPhaseSerializer(serializers.ModelSerializer):
#     project_name = serializers.CharField(source="project.name", read_only=True)
#
#     class Meta:
#         model = ProjectPhase
#         fields = "__all__"
#
#
# class BoqItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BoqItem
#         fields = [
#             "id", "item_no", "description", "unit", "quantity", "rate", "amount",
#             "item_type", "order"
#         ]
#
#
# class BoqSectionSerializer(serializers.ModelSerializer):
#     items = BoqItemSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = BoqSection
#         fields = ["id", "code", "title", "order", "items"]
#
#
# class BoqSerializer(serializers.ModelSerializer):
#     sections = BoqSectionSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Boq
#         fields = ["id", "code", "title", "description", "is_primary", "sections"]

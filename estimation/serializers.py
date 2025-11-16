from .models import *
from rest_framework import serializers
# from core.serializers import ProfileSerializer
# from projects.serializers import SubPhaseSerializer


class EstimationSerializer(serializers.ModelSerializer):
    # subphase = SubPhaseSerializer(read_only=True)
    # prepared_by = ProfileSerializer(read_only=True)
    # approved_by = ProfileSerializer(read_only=True)

    class Meta:
        model = Estimation
        fields = "__all__"


class BOQSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)

    class Meta:
        model = BOQ
        fields = ["id", "name", "file_path", "file_hash"]


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name"]


class SubsectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subsection
        fields = ["id", "name"]


# ───────────────────────── Materials nested under BOQItem ─────────────────────────
class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = [
            "id",
            "name",
            "rate",
            "wastage",
            "u_rate",
            "amount",
        ]
        read_only_fields = ["amount"]  # it's computed in model.save()


class BOQItemSerializer(serializers.ModelSerializer):
    # Nest materials for each BOQ item
    materials = MaterialSerializer(many=True, read_only=True)

    class Meta:
        model = BOQItem
        fields = [
            "id",
            "description",
            "unit",
            "quantity",
            "rate",
            "amount",

            # computed / rollup fields
            "dry_cost",
            "unit_rate",
            "prelimin",
            "boq_amount",

            # labour
            "labor_rate",
            "labor_hours",
            "labor_amount",

            # plant
            "plant_rate",
            "plant_amount",

            # subcontract
            "subcontract_rate",
            "subcontract_amount",

            # metadata
            "sort_order",
            "factor",

            # nested
            "materials",
        ]


class DetailedSubsectionSerializer(serializers.ModelSerializer):
    items = BOQItemSerializer(many=True, read_only=True)

    class Meta:
        model = Subsection
        fields = ["id", "name", "items"]


class DetailedSectionSerializer(serializers.ModelSerializer):
    subsections = DetailedSubsectionSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = ["id", "name", "factor", "subsections"]


class BOQDetailSerializer(serializers.ModelSerializer):
    sections = DetailedSectionSerializer(many=True, read_only=True)

    class Meta:
        model = BOQ
        fields = ["id", "name", "sections"]


# ───────────────────────── Partial cost updates for BOQItem ───────────────────────
class BOQItemCostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOQItem
        fields = [
            "id",
            "description",

            # editable inputs
            "labor_rate",
            "labor_hours",
            "plant_rate",
            "subcontract_rate",

            # computed outputs (read-only)
            "labor_amount",
            "plant_amount",
            "subcontract_amount",
            "dry_cost",
            "unit_rate",
            "boq_amount",
        ]
        read_only_fields = [
            "labor_amount",
            "plant_amount",
            "subcontract_amount",
            "dry_cost",
            "unit_rate",
            "boq_amount",
        ]

    def update(self, instance, validated_data):
        # Apply provided fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        # Trigger model-level rollups (your BOQItem.save handles this)
        instance.save()
        return instance




class MaterialUpsertSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    name = serializers.CharField()
    rate = serializers.FloatField(required=False, allow_null=True)
    wastage = serializers.FloatField(required=False, allow_null=True)
    unit_rate = serializers.FloatField(required=False, allow_null=True)  # FE key
    amount = serializers.FloatField(required=False, allow_null=True)

class BOQItemEstimationUpsertSerializer(serializers.Serializer):
    # identity
    item_id = serializers.IntegerField()

    # optional item meta
    description = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.FloatField(required=False)

    # section factor
    section_factor = serializers.FloatField(required=False)

    # rollup + mapping
    rate = serializers.FloatField(required=False)         # final_rate
    amount = serializers.FloatField(required=False)       # total_amount

    labour_unit_rate = serializers.FloatField(required=False)  # FE spelling
    labour_hours = serializers.FloatField(required=False)
    labour_amount = serializers.FloatField(required=False)

    plant_rate = serializers.FloatField(required=False)
    plant_amount = serializers.FloatField(required=False)

    subcontract_rate = serializers.FloatField(required=False)
    subcontract_amount = serializers.FloatField(required=False)

    dry_cost = serializers.FloatField(required=False)
    unit_rate = serializers.FloatField(required=False)     # estimated_unit_rate
    factor = serializers.FloatField(required=False)
    prelimin = serializers.FloatField(required=False)
    total_amount = serializers.FloatField(required=False)  # duplicate of amount; ok

    materials = MaterialUpsertSerializer(many=True, required=False)

    def save(self, **kwargs):
        item_id = self.validated_data['item_id']
        item = BOQItem.objects.select_related('subsection__section').get(id=item_id)

        vd = self.validated_data

        # 1) update section factor (if provided)
        if 'section_factor' in vd and item.subsection and item.subsection.section:
            section = item.subsection.section
            section.factor = vd['section_factor']
            section.save(update_fields=['factor'])

        # 2) patch BOQItem core fields (only provided keys)
        field_map = {
            'description': 'description',
            'unit': 'unit',
            'quantity': 'quantity',

            # inputs
            'labour_unit_rate': 'labor_rate',
            'labour_hours': 'labor_hours',
            'labour_amount': 'labor_amount',

            'plant_rate': 'plant_rate',
            'plant_amount': 'plant_amount',

            'subcontract_rate': 'subcontract_rate',
            'subcontract_amount': 'subcontract_amount',

            # computed/rollups
            'dry_cost': 'dry_cost',
            'unit_rate': 'unit_rate',
            'factor': 'factor',
            'prelimin': 'prelimin',

            # explicit mapping of final to item fields
            'rate': 'rate',
            'amount': 'amount',
            'total_amount': 'amount',  # if FE sends both, 'amount' wins later
        }

        for src, dst in field_map.items():
            if src in vd and vd[src] is not None:
                setattr(item, dst, vd[src])

        # 3) save item (rollups are in model.save)
        item.save()

        # 4) upsert materials (replace-all strategy)
        materials = vd.get('materials')
        if isinstance(materials, list):
            # clear and recreate for simplicity; can be replaced with diff-based upsert
            item.materials.all().delete()
            bulk = []
            for m in materials:
                bulk.append(Material(
                    boq_item=item,
                    name=m.get('name', ''),
                    rate=m.get('rate'),
                    wastage=m.get('wastage'),
                    # align keys: FE sends 'unit_rate'; Model uses 'u_rate'
                    u_rate=m.get('unit_rate'),
                    amount=m.get('amount'),   # trust FE snapshot
                ))
            Material.objects.bulk_create(bulk)

            # after materials change, recompute item rollups
            item.save()

        return item
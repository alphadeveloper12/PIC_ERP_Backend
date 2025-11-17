# planning/services/p6_extractor.py

from planning.models import P6Activity
import pandas as pd
from django.db import transaction


class P6Extractor:

    @staticmethod
    def extract_and_save(file):
        # Load workbook
        xls = pd.ExcelFile(file)

        # Required sheets
        task = pd.read_excel(xls, "TASK")
        wbs = pd.read_excel(xls, "PROJWBS")
        actv = pd.read_excel(xls, "ACTVCODE")
        taskactv = pd.read_excel(xls, "TASKACTV")

        # Merge same as original logic
        merged = (
            task.merge(wbs, on="wbs_id", how="left")
                .merge(taskactv, on="task_id", how="left")
                .merge(actv, on="actv_code_id", how="left")
        )

        # Auto-detect activity code column
        possible_cols = ["actv_short_name", "actv_code_short", "actv_code", "actv_code_name"]
        found_col = next((c for c in possible_cols if c in merged.columns), None)

        extracted = merged.rename(columns={
            "task_code": "activity_id",
            "task_name": "activity_name",
            found_col: "activity_code" if found_col else None,
            "wbs_short_name": "wbs_code",
            "wbs_name": "wbs_name",
        })

        # Clear old data
        P6Activity.objects.all().delete()

        # Bulk create activities (high performance)
        activities = [
            P6Activity(
                task_id=row["task_id"],
                activity_id=row["activity_id"],
                activity_name=row["activity_name"],
                wbs_code=row.get("wbs_code"),
                wbs_name=row.get("wbs_name"),
                activity_code=row.get("activity_code", ""),
            )
            for _, row in extracted.iterrows()
        ]

        # Insert in batches
        with transaction.atomic():
            P6Activity.objects.bulk_create(activities, batch_size=5000)

        return extracted

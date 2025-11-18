# planning/services/p6_extractor.py

from planning.models import P6Activity
import pandas as pd
from django.db import transaction, connection
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class P6Extractor:

    @staticmethod
    def remove_duplicates():
        """
        Remove duplicate P6 activities using SQL for best performance.
        Duplicates removed based on task_id.
        Keeps the first record and deletes all others.
        """

        logger.info("Removing duplicate P6Activity entries...")

        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM planning_p6activity
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM planning_p6activity
                    GROUP BY task_id
                );
            """)

        logger.info("Duplicate P6 records removed successfully.")

    @staticmethod
    def extract_and_save(file):
        # Load workbook
        xls = pd.ExcelFile(file)

        # Required sheets
        task = pd.read_excel(xls, "TASK")
        wbs = pd.read_excel(xls, "PROJWBS")
        actv = pd.read_excel(xls, "ACTVCODE")
        taskactv = pd.read_excel(xls, "TASKACTV")

        # Merge logic
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
        logger.info("Clearing previous P6Activity table...")
        P6Activity.objects.all().delete()

        # Bulk insert new activities
        logger.info("Inserting new P6Activity records...")
        activities = [
            P6Activity(
                task_id=row["task_id"],
                activity_id=row["activity_id"],
                activity_name=row["activity_name"],
                wbs_code=row.get("wbs_code"),
                wbs_name=row.get("wbs_name"),
                activity_code=row.get("activity_code", ""),
            )
            for _, row in tqdm(extracted.iterrows(), total=extracted.shape[0], desc="Processing P6 Activities")
        ]

        with transaction.atomic():
            P6Activity.objects.bulk_create(activities, batch_size=5000)

        logger.info(f"P6 extraction inserted {len(activities)} records.")

        # --------------------------------------------
        # REMOVE DUPLICATES BEFORE MATCHING
        # --------------------------------------------
        P6Extractor.remove_duplicates()

        return extracted

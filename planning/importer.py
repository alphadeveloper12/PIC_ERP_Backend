from django.db import transaction
from .models import Schedule, WorkBreakdownItem, Task


class XerImporter:
    """
    Imports parsed Primavera XER data into Django models under a given Planning.
    """

    # -----------------------------------------------------------------------
    # 1️⃣ Temporary parser — replace this with your real .xer parser later
    # -----------------------------------------------------------------------
    def parse_xer(self, file):
        """
        Dummy parser used for testing. Replace with real parser later.

        It simply returns sample structured data so you can confirm
        your Celery + DB pipeline works correctly.
        """
        return {
            "schedule": {
                "external_id": "SCHED001",
                "name": "Demo Construction Schedule",
                "start_date": None,
                "finish_date": None,
                "calendar_name": "Standard Calendar"
            },
            "wbs": [
                {"external_id": "W1", "name": "Foundation", "level": 1},
                {"external_id": "W2", "name": "Structure", "level": 1},
                {"external_id": "W3", "name": "Finishes", "level": 1},
            ],
            "tasks": [
                {"external_id": "T1", "name": "Excavation", "wbs_external_id": "W1", "duration": 5},
                {"external_id": "T2", "name": "Pour Concrete", "wbs_external_id": "W1", "duration": 7},
                {"external_id": "T3", "name": "Brickwork", "wbs_external_id": "W2", "duration": 10},
                {"external_id": "T4", "name": "Painting", "wbs_external_id": "W3", "duration": 6},
            ]
        }

    # -----------------------------------------------------------------------
    # 2️⃣ Core import logic — safely creates all dependent models
    # -----------------------------------------------------------------------
    @transaction.atomic
    def import_data(self, parsed, planning):
        """
        Safely imports all parsed entities (Schedule → WBS → Tasks)
        inside one atomic transaction.
        """

        # ---- Create or get Schedule ----
        sched_data = parsed.get("schedule", {})
        schedule, _ = Schedule.objects.get_or_create(
            planning=planning,
            external_id=sched_data.get("external_id", "DEFAULT"),
            defaults={
                "name": sched_data.get("name", "Imported Schedule"),
                "start_date": sched_data.get("start_date"),
                "finish_date": sched_data.get("finish_date"),
                "calendar_name": sched_data.get("calendar_name", ""),
            },
        )

        # ---- Create Work Breakdown Structure (WBS) ----
        wbs_objs = []
        for w in parsed.get("wbs", []):
            wbs_objs.append(
                WorkBreakdownItem(
                    schedule=schedule,
                    external_id=w["external_id"],
                    name=w["name"],
                    short_name=w.get("short_name"),
                    level=w.get("level", 0),
                    weight=w.get("weight"),
                    status=w.get("status"),
                )
            )

        WorkBreakdownItem.objects.bulk_create(wbs_objs, ignore_conflicts=True)

        # Build mapping for FK assignments
        wbs_map = {
            w.external_id: w
            for w in WorkBreakdownItem.objects.filter(schedule=schedule)
        }

        # ---- Create Tasks linked to WBS ----
        task_objs = []
        for t in parsed.get("tasks", []):
            wbs_ref = wbs_map.get(t.get("wbs_external_id"))
            if not wbs_ref:
                continue

            task_objs.append(
                Task(
                    wbs_item=wbs_ref,
                    external_id=t["external_id"],
                    name=t["name"],
                    start_date=t.get("start_date"),
                    finish_date=t.get("finish_date"),
                    duration=t.get("duration"),
                    percent_complete=t.get("percent_complete"),
                    status=t.get("status"),
                    critical_flag=t.get("critical_flag", False),
                )
            )

        Task.objects.bulk_create(task_objs, ignore_conflicts=True)

        # ---- Summary for job tracking ----
        return {
            "schedule": schedule.name,
            "imported_wbs": len(wbs_objs),
            "imported_tasks": len(task_objs),
        }

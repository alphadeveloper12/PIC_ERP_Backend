from planning.models import P6Activity
import pandas as pd

class P6Extractor:

    @staticmethod
    def extract_and_save(file):
        print("\n======================")
        print("📌 DEBUG: Loading Excel File")
        print("======================")

        try:
            xls = pd.ExcelFile(file)
        except Exception as e:
            print("❌ ERROR: Failed to read Excel:", e)
            raise

        print("📄 Sheets Found:", xls.sheet_names)

        # --- Load sheets with debug ---
        def safe_read(sheet_name):
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                print(f"\n📘 Sheet '{sheet_name}' loaded successfully.")
                print(f"➡ Columns in '{sheet_name}': {list(df.columns)}")
                return df
            except Exception as e:
                print(f"\n❌ ERROR: Failed to read sheet '{sheet_name}': {e}")
                return None

        task = safe_read("TASK")
        wbs = safe_read("PROJWBS")
        actv = safe_read("ACTVCODE")
        taskactv = safe_read("TASKACTV")

        # Validate sheets exist
        if task is None or wbs is None or actv is None or taskactv is None:
            raise Exception("❌ One or more required sheets failed to load.")

        print("\n======================")
        print("📌 DEBUG: Merging Sheets")
        print("======================")

        merged = (
            task.merge(wbs, on="wbs_id", how="left")
                .merge(taskactv, on="task_id", how="left")
                .merge(actv, on="actv_code_id", how="left")
        )

        print("\n📑 Columns After Merge:", list(merged.columns))

        # Debug: check if critical columns exist
        critical_cols = [
            "task_id",
            "task_code",
            "task_name",
            "wbs_short_name",
            "wbs_name",
            "actv_short_name",   # primary expected from ACTVCODE
            "actv_code",         # alternative names
            "actv_code_short",
            "actv_code_name"
        ]

        print("\n🔍 Checking Missing Columns:")
        for col in critical_cols:
            if col not in merged.columns:
                print(f"⚠ MISSING: '{col}'")

        # Try to auto-select activity code column
        possible_cols = ["actv_short_name", "actv_code_short", "actv_code", "actv_code_name"]
        found_col = next((c for c in possible_cols if c in merged.columns), None)

        if found_col:
            print(f"\n✅ Activity code detected using column: {found_col}")
        else:
            print("\n❌ No activity code column found! Will set empty values.")
            found_col = None

        # Apply dynamic renaming
        extracted = merged.rename(columns={
            "task_code": "activity_id",
            "task_name": "activity_name",
            found_col: "activity_code" if found_col else None,
            "wbs_short_name": "wbs_code",
            "wbs_name": "wbs_name",
        })

        print("\n📌 DEBUG: Final Extracted Columns:", list(extracted.columns))

        # Clear existing data
        P6Activity.objects.all().delete()

        print("\n======================")
        print("📌 Saving Activities to DB")
        print("======================")

        for _, r in extracted.iterrows():
            P6Activity.objects.create(
                task_id=r.get("task_id"),
                activity_id=r.get("activity_id"),
                activity_name=r.get("activity_name"),
                wbs_code=r.get("wbs_code"),
                wbs_name=r.get("wbs_name"),
                activity_code=r.get("activity_code", ""),
            )

        print("\n🎉 SUCCESS: P6 Data Imported")
        print("======================\n")

        return extracted

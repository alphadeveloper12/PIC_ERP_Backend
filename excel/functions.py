import pandas as pd

# ===== Config =====
REQUIRED_COLS = {
    "item_no", "description", "unit", "quantity", "rate",
    "material_rate", "material_wastage", "plant_rate",
    "labour_hours", "subcontract_rate",
    "others_1_qty", "others_1_rate", "others_2_qty", "others_2_rate",
    "dry_cost", "unit_rate", "prelimin", "boq_amount",
    "actual_qty", "actual_amount", "factor", "material"
}

ALIASES = {
    "labour_hrs": "labour_hours",
    "labor_hours": "labour_hours",
    "u_rate": "unit_rate",
    "prelim": "prelimin",
    "boq": "boq_amount",
    "materials": "material",
    "plant": "plant_rate",
    "description_of_work": "description",
    "desc": "description",
}

BULK_SIZE = 1000
HEADER_ROWS_TO_TRY = 3         # try first 3 rows as header
SAMPLE_ROWS_PER_SHEET = 10     # sample a few rows per sheet to score
REPLACE_MATERIALS = True       # True: delete + re-insert per item on each upload
# =================================================

def _norm(s: str) -> str:
    return str(s).strip().replace("\n", "").replace(" ", "_").lower()

def _norm_cols(cols):
    return [_norm(c) for c in cols]

def _alias_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: ALIASES.get(c, c) for c in df.columns})

def _score_cols(cols):
    return len(set(cols) & REQUIRED_COLS)

def choose_sheet_fast(fileobj):
    """
    Returns (sheet_name, header_row).
    Uses sampling to avoid loading entire workbook for every sheet.
    """
    try:
        fileobj.seek(0)
    except Exception:
        pass

    xls = pd.ExcelFile(fileobj)
    best = (None, None, -1)
    for sheet in xls.sheet_names:
        for hdr in range(HEADER_ROWS_TO_TRY):
            try:
                df = pd.read_excel(
                    xls, sheet_name=sheet, header=hdr,
                    dtype=str, nrows=SAMPLE_ROWS_PER_SHEET
                )
            except Exception:
                continue
            df.columns = _norm_cols(df.columns)
            df = _alias_df(df)
            sc = _score_cols(df.columns)
            if "description" in df.columns and sc > best[2]:
                best = (sheet, hdr, sc)

    if best[0] is None:
        return xls.sheet_names[0], 0
    return best[0], best[1]

def to_float_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    ).fillna(0.0)

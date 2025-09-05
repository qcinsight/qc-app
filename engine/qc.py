import pandas as pd
import json
from pathlib import Path

# Load rules once from JSON
RULES = json.loads(Path("engine/rules.json").read_text())

# Columns that would indicate PHI (we block if seen)
PHI_BLOCKLIST = ["mrn", "dob", "patient", "name", "address", "ssn"]

def check_phi_columns(df: pd.DataFrame):
    """Raise if any column name looks like PHI."""
    cols = [c.lower() for c in df.columns]
    if any(any(b in c for b in PHI_BLOCKLIST) for c in cols):
        raise ValueError("File appears to contain PHI-like columns. Please remove and re-upload de-identified data.")

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Basic header cleanup (spaces -> underscores)."""
    rename_map = {c: c.strip().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=rename_map)
    return df

def summarize_qc(df: pd.DataFrame):
    """
    Expect at least these columns:
      SampleID, SampleType, Block, Count, IntraCV, InterCV, PF, Occupancy, SampleQC
    Returns:
      block_fail_frac (per-block fail fraction + pass flag),
      ctl_summary (counts of external vs internal-like)
    """
    required = ["SampleID","SampleType","Block","Count","IntraCV","InterCV","PF","Occupancy","SampleQC"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Per-block % of failing samples (based on SampleQC == 'fail')
    fail_series = (df["SampleQC"].astype(str).str.lower() == "fail")
    block_fail_frac = (
        df.assign(fail=fail_series)
          .groupby("Block", dropna=False)["fail"].mean()
          .rename("sample_fail_fraction")
          .reset_index()
    )
    thresh = RULES.get("fail_if_sample_fail_fraction_gt", 0.1667)
    block_fail_frac["block_pass"] = block_fail_frac["sample_fail_fraction"] <= thresh

    # External controls vs everything else (simple, safe first pass)
    external_mask = df["SampleType"].astype(str).str.lower().isin([
        "plate control","sample control","negative control",
        "plate_control","sample_control","negative_control"
    ])
    external = df[external_mask]
    internal_like = df[~external_mask]

    ctl_summary = pd.DataFrame({
        "external_controls_n": [len(external)],
        "internal_like_n": [len(internal_like)]
    })

    return block_fail_frac, ctl_summary

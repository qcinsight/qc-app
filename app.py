from typing import Tuple
import pandas as pd

def summarize_qc(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Column‑agnostic QC summary that supports both proteomic and genomic demos.
    Requires only SampleID. Everything else is optional.
    Returns: (block_or_global_summary_df, control_summary_df)
    """
    cols = set(df.columns)

    if "SampleID" not in cols:
        raise ValueError("Missing required column: 'SampleID'")

    # Pick a grouping key if present
    group_key = next((c for c in ["Block","Plate","Run","Batch","Lane","Flowcell"] if c in cols), None)

    # Derive fail fraction if SampleQC exists, else provide counts by group/global
    if "SampleQC" in cols:
        fail_flag = df["SampleQC"].astype(str).str.lower().eq("fail")
        if group_key:
            block = (
                df.assign(fail=fail_flag)
                  .groupby(group_key)["fail"].mean()
                  .rename("sample_fail_fraction").reset_index()
            )
        else:
            block = pd.DataFrame({"Group":["All"], "sample_fail_fraction":[float(fail_flag.mean())]})
        # Threshold (fixed default)
        block["block_pass"] = block["sample_fail_fraction"] <= 0.1667
    else:
        # No QC label available: just report sample counts by group or globally
        if group_key:
            block = df.groupby(group_key).size().rename("n_samples").reset_index()
        else:
            block = pd.DataFrame({"Group":["All"], "n_samples":[len(df)]})

    # Control summary – count external vs internal-like (metric not required)
    if "SampleType" in cols:
        lower = df["SampleType"].astype(str).str.lower()
        external = lower.isin([
            "plate control","sample control","negative control","positive control",
            "plate_control","sample_control","negative_control","positive_control"
        ])
        ctl_summary = pd.DataFrame({
            "external_controls_n": [int(external.sum())],
            "internal_like_n": [int((~external).sum())]
        })
    else:
        ctl_summary = pd.DataFrame({"external_controls_n":[0], "internal_like_n":[len(df)]})

    return block, ctl_summary
import pandas as pd

def summarize_qc(df: pd.DataFrame):
    # Required columns: SampleID, optionally SampleQC
    required_cols = ['SampleID']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Optional SampleQC column
    sample_qc_present = 'SampleQC' in df.columns

    # Identify numeric metrics present in the data
    numeric_metrics = ['Count', 'PF', 'Occupancy', 'ReadDepth', 'MappedReads', 'QuantValue']
    metrics_present = [col for col in numeric_metrics if col in df.columns]

    if not metrics_present:
        raise ValueError("No numeric metrics found (expected one of Count, PF, Occupancy, ReadDepth, MappedReads, QuantValue)")

    # Prepare block summary
    block_cols = ['Block'] if 'Block' in df.columns else []
    group_cols = block_cols if block_cols else []

    # Aggregate metrics by block
    block_summary = df.groupby(group_cols)[metrics_present].agg(['mean', 'std', 'count']) if group_cols else pd.DataFrame()
    if not group_cols:
        # If no Block column, summarize over all samples
        block_summary = df[metrics_present].agg(['mean', 'std', 'count']).to_frame().T

    # Flatten MultiIndex columns if any
    if isinstance(block_summary.columns, pd.MultiIndex):
        block_summary.columns = ['_'.join(col).strip() for col in block_summary.columns.values]
    block_summary = block_summary.reset_index()

    # Prepare control summary
    ctl_summary = pd.DataFrame()
    if 'SampleType' in df.columns:
        controls = df[df['SampleType'].str.contains('control', case=False, na=False)]
        if not controls.empty:
            ctl_summary = controls.groupby('SampleType')[metrics_present].agg(['mean', 'std', 'count'])
            if isinstance(ctl_summary.columns, pd.MultiIndex):
                ctl_summary.columns = ['_'.join(col).strip() for col in ctl_summary.columns.values]
            ctl_summary = ctl_summary.reset_index()
        else:
            # No controls found, return empty DataFrame with appropriate columns
            ctl_summary = pd.DataFrame(columns=['SampleType'] + [f"{m}_mean" for m in metrics_present] + [f"{m}_std" for m in metrics_present] + [f"{m}_count" for m in metrics_present])
    else:
        # No SampleType column, return empty DataFrame with appropriate columns
        ctl_summary = pd.DataFrame(columns=['SampleType'] + [f"{m}_mean" for m in metrics_present] + [f"{m}_std" for m in metrics_present] + [f"{m}_count" for m in metrics_present])

    return block_summary, ctl_summary
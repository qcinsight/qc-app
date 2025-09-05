def summarize_qc(df: pd.DataFrame):
    """
    Return (block_or_global_summary_df, control_summary_df) while being tolerant to missing columns.
    - Required: SampleID (string)
    - Optional grouping key: Block/Plate/Run/Batch/Lane/Flowcell
    - Optional QC flag: SampleQC
    - Optional metrics: Count, IntraCV, InterCV, PF, Occupancy, QuantValue, ReadDepth, MappedReads, DupRate, Coverage
    """
    cols = set(df.columns)

    # Basic sanity
    if "SampleID" not in cols:
        raise ValueError("Missing required column: SampleID")

    # Determine grouping key if present
    CANDIDATE_GROUPS = ["Block","Plate","Run","Batch","Lane","Flowcell"]
    group_key = next((c for c in CANDIDATE_GROUPS if c in cols), None)

    # Fail fraction table (by group if possible, otherwise global)
    fail_series = None
    if "SampleQC" in cols:
        if group_key:
            fail_series = (
                df.assign(fail=(df["SampleQC"].astype(str).str.lower()=="fail"))
                  .groupby(group_key)["fail"].mean()
                  .rename("sample_fail_fraction")
            )
            block_fail_frac = fail_series.reset_index()
        else:
            frac = float((df["SampleQC"].astype(str).str.lower()=="fail").mean())
            block_fail_frac = pd.DataFrame({"group":["All"], "sample_fail_fraction":[frac]})
            block_fail_frac.rename(columns={"group": "Group" }, inplace=True)
    else:
        # No QC flag; report counts per group or global count
        if group_key:
            block_fail_frac = (
                df.groupby(group_key)
                  .size()
                  .rename("n_samples")
                  .reset_index()
            )
        else:
            block_fail_frac = pd.DataFrame({"Group":["All"], "n_samples":[len(df)]})

    # If we computed sample_fail_fraction, decide pass/fail vs rules if present
    if "sample_fail_fraction" in block_fail_frac.columns:
        thresh = RULES.get("fail_if_sample_fail_fraction_gt", 0.1667)
        block_fail_frac["block_pass"] = block_fail_frac["sample_fail_fraction"] <= thresh

    # Control summary (counts only; do not assume Count exists)
    lower = df["SampleType"].astype(str).str.lower() if "SampleType" in cols else pd.Series([], dtype=str)
    external_mask = lower.isin(["plate control","sample control","negative control","plate_control","sample_control","negative_control","positive control","positive_control"]) if len(lower) else pd.Series([], dtype=bool)
    external_n = int(external_mask.sum()) if len(lower) else 0
    internal_like_n = int((~external_mask).sum()) if len(lower) else 0
    ctl_summary = pd.DataFrame({"external_controls_n":[external_n], "internal_like_n":[internal_like_n]})

    return block_fail_frac, ctl_summary

def boxplot_counts_by_block(df: pd.DataFrame, outpath: str):
    # Choose a numeric metric automatically
    metric_candidates = ["Count","ReadDepth","MappedReads","QuantValue"]
    metric = next((m for m in metric_candidates if m in df.columns), None)
    group_key_candidates = ["Block","Plate","Run","Batch","Lane","Flowcell"]
    group_key = next((g for g in group_key_candidates if g in df.columns), None)

    plt.figure()
    if metric and group_key and df[metric].dtype != "O":
        ax = df.boxplot(column=metric, by=group_key, grid=False, rot=0)
        plt.title(f"{metric} by {group_key}")
        plt.suptitle("")
        plt.xlabel(group_key); plt.ylabel(metric)
    elif metric:
        ax = df.boxplot(column=metric, grid=False, rot=0)
        plt.title(metric)
        plt.xlabel(""); plt.ylabel(metric)
    else:
        plt.text(0.5,0.5,"No numeric metric found (expected one of Count/ReadDepth/MappedReads/QuantValue)", ha="center", va="center")
        plt.axis("off")
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()

def heatmap_external_controls(df: pd.DataFrame, outpath: str):
    # prefer Count; fall back to ReadDepth, MappedReads, QuantValue
    value_candidates = ["Count","ReadDepth","MappedReads","QuantValue"]
    value_col = next((v for v in value_candidates if v in df.columns), None)
    if "SampleType" not in df.columns:
        # produce a neutral image so PDF step doesn’t fail
        plt.figure(); plt.text(0.5,0.5,"No SampleType column for control heatmap", ha="center", va="center")
        plt.axis("off")
    else:
        data = df[df["SampleType"].astype(str).str.lower().isin(
            ["plate control","sample control","negative control","positive control","plate_control","sample_control","negative_control","positive_control"]
        )]
        if data.empty or value_col is None:
            plt.figure(); plt.text(0.5,0.5,"No external controls or metric for heatmap", ha="center", va="center")
            plt.axis("off")
        else:
            pivot = data.pivot_table(index=df.get("Block", pd.Series(["All"]*len(data))), 
                                     columns="SampleType", values=value_col, aggfunc="median").fillna(0)
            plt.imshow(pivot.values, aspect="auto")
            plt.xticks(range(pivot.shape[1]), pivot.columns, rotation=45, ha="right")
            plt.yticks(range(pivot.shape[0]), pivot.index)
            plt.title(f"Median {value_col} (External Controls)")
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()

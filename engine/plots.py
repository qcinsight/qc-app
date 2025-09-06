import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def _pick_first_present(candidates, cols):
    return next((c for c in candidates if c in cols), None)

def boxplot_counts_by_block(
    df: pd.DataFrame,
    outpath: str,
    metric: str | None = None,
    group_key: str | None = None,
):
    if metric is None:
        metric = _pick_first_present(
            ["Count","ReadDepth","MappedReads","PF","Occupancy","QuantValue","Coverage"], df.columns
        )
    if group_key is None:
        group_key = _pick_first_present(
            ["Block","Plate","Run","Batch","Lane","Flowcell","LibraryType","SampleType"], df.columns
        )

    plt.figure()
    if metric is not None and pd.api.types.is_numeric_dtype(df[metric]):
        if group_key and group_key in df.columns:
            df.boxplot(column=metric, by=group_key, grid=False, rot=0)
            plt.title(f"{metric} by {group_key}")
            plt.suptitle("")
            plt.xlabel(group_key); plt.ylabel(metric)
        else:
            df.boxplot(column=metric, grid=False, rot=0)
            plt.title(metric); plt.xlabel(""); plt.ylabel(metric)
    else:
        plt.text(0.5,0.5,"No numeric metric available to plot", ha="center", va="center")
        plt.axis("off")

    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(outpath, dpi=200); plt.close()

def heatmap_external_controls(
    df: pd.DataFrame,
    outpath: str,
    value_col: str | None = None,
    group_key: str | None = None,
):
    if value_col is None:
        value_col = _pick_first_present(
            ["Count","ReadDepth","MappedReads","PF","Occupancy","QuantValue","Coverage"], df.columns
        )

    if "SampleType" not in df.columns:
        plt.figure(); plt.text(0.5,0.5,"No SampleType column for control heatmap", ha="center", va="center")
        plt.axis("off")
    else:
        data = df[df["SampleType"].astype(str).str.lower().isin(
            ["plate control","sample control","negative control","positive control",
             "plate_control","sample_control","negative_control","positive_control"]
        )]
        if data.empty or value_col is None or not pd.api.types.is_numeric_dtype(df[value_col]):
            plt.figure(); plt.text(0.5,0.5,"No external controls or numeric metric", ha="center", va="center")
            plt.axis("off")
        else:
            if group_key is None or group_key not in df.columns:
                index_series = pd.Series(["All"]*len(data), index=data.index)
            else:
                index_series = data[group_key].astype(str)

            pivot = data.pivot_table(index=index_series, columns="SampleType",
                                     values=value_col, aggfunc="median").fillna(0)
            plt.figure()
            plt.imshow(pivot.values, aspect="auto")
            plt.xticks(range(pivot.shape[1]), pivot.columns, rotation=45, ha="right")
            plt.yticks(range(pivot.shape[0]), pivot.index)
            plt.title(f"Median {value_col} (External Controls)")

    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(outpath, dpi=200); plt.close()

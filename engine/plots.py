import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def boxplot_counts_by_block(df: pd.DataFrame, outpath: str):
    fig, ax = plt.subplots()
    df.boxplot(column="Count", by="Block", grid=False, rot=0, ax=ax)
    ax.set_title("Counts by Block"); plt.suptitle("")
    ax.set_xlabel("Block"); ax.set_ylabel("Count")
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(outpath, dpi=200)
    return fig

def heatmap_external_controls(df: pd.DataFrame, outpath: str):
    data = df[df["SampleType"].astype(str).str.lower().isin(
        ["plate control","sample control","negative control",
         "plate_control","sample_control","negative_control"]
    )]
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots()
    if data.empty:
        ax.text(0.5, 0.5, "No external controls", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout(); fig.savefig(outpath, dpi=200)
        return fig

    pivot = data.pivot_table(index="Block", columns="SampleType",
                             values="Count", aggfunc="median").fillna(0)

    im = ax.imshow(pivot.values, aspect="auto")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Median Counts")
    ax.set_xticks(range(pivot.shape[1])); ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(pivot.shape[0])); ax.set_yticklabels(pivot.index)
    ax.set_title("Median Counts (External Controls)")
    fig.tight_layout()
    fig.savefig(outpath, dpi=200)
    return fig

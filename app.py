import streamlit as st
import pandas as pd
from pathlib import Path
from engine.qc import check_phi_columns, standardize_columns, summarize_qc
from engine.plots import boxplot_counts_by_block, heatmap_external_controls
from engine.pdf import build_pdf

st.set_page_config(page_title="QC Report Builder", layout="centered")
st.title("QC Report Builder (De-identified Only)")
st.caption("Upload a CSV/Parquet export → get a 1-page PDF with summary + plots. No PHI.")

uploaded = st.file_uploader("Upload CSV or Parquet", type=["csv","parquet"])

if uploaded:
    # read file
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        import pyarrow.parquet as pq, io
        table = pq.read_table(io.BytesIO(uploaded.read()))
        df = table.to_pandas()

    try:
        check_phi_columns(df)
        df = standardize_columns(df)
        st.write("Preview:", df.head())

        block_summary, ctl_summary = summarize_qc(df)

        outputs = Path("outputs"); outputs.mkdir(exist_ok=True)
        p1 = outputs / "box_counts.png"
        p2 = outputs / "heatmap_controls.png"
        boxplot_counts_by_block(df, str(p1))
        heatmap_external_controls(df, str(p2))

                # --- show summaries ---
        st.subheader("Block summary")
        st.dataframe(block_summary)

        st.subheader("Control summary")
        st.table(ctl_summary)

        # --- generate + show plots ---
        outputs = Path("outputs"); outputs.mkdir(exist_ok=True)
        p1 = outputs / "box_counts.png"
        p2 = outputs / "heatmap_controls.png"

        fig1 = boxplot_counts_by_block(df, str(p1))
        fig2 = heatmap_external_controls(df, str(p2))

        st.subheader("Plots")
        st.pyplot(fig1)
        st.pyplot(fig2)

        # --- build PDF as before ---
        pdf_path = outputs / "QC_Report.pdf"
        build_pdf(str(pdf_path), "engine/rules.json",
                  block_summary, ctl_summary, str(p1), str(p2))

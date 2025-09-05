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

        # --- summaries ---
        block_summary, ctl_summary = summarize_qc(df)

        # --- make outputs dir & plot files ---
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

        # --- show plots saved to disk ---
        st.subheader("Plots")
        if p1.exists():
            st.image(str(p1), caption="Counts by Group/Block", use_column_width=True)
        if p2.exists():
            st.image(str(p2), caption="External Controls Heatmap", use_column_width=True)

        # --- build PDF & download ---
        pdf_path = outputs / "QC_Report.pdf"
        build_pdf(str(pdf_path), "engine/rules.json", block_summary, ctl_summary, str(p1), str(p2))
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", data=f.read(), file_name="QC_Report.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Error during QC processing: {e}")

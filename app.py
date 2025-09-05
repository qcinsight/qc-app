import streamlit as st
import pandas as pd
from pathlib import Path
from engine.qc import check_phi_columns, standardize_columns, summarize_qc
from engine.plots import boxplot_counts_by_block, heatmap_external_controls
from engine.pdf import build_pdf

st.set_page_config(page_title="QC Report Builder", layout="centered")
st.title("QC Report Builder (De-identified Only)")
st.caption("Upload a CSV/Parquet export → get a 1-page PDF with summary + plots. No PHI.")

# Optional demo dataset so users can try without their own data
demo_type = st.selectbox("Try with demo data", ["None", "Proteomic (Olink)", "Genomic"])
use_demo = demo_type != "None"

uploaded = st.file_uploader("Upload CSV or Parquet", type=["csv","parquet"])

if uploaded or use_demo:
    # read file (uploaded or demo)
    if use_demo and not uploaded:
        if demo_type == "Proteomic (Olink)":
            demo_path = Path("samples/demo_olink.csv")
            if demo_path.exists():
                df = pd.read_csv(demo_path)
                st.info("Using bundled Olink proteomic demo dataset.")
            else:
                if "demo_notice_shown" not in st.session_state or not st.session_state["demo_notice_shown"]:
                    st.info("Using built-in Olink demo rows (add samples/demo_olink.csv to customize).")
                    st.session_state["demo_notice_shown"] = True
                df = pd.DataFrame({
                    "SampleID": [f"S{i:03d}" for i in range(1, 13)],
                    "SampleType": ["sample"]*10 + ["plate control","negative control"],
                    "Block": ["A"]*6 + ["B"]*6,
                    "Count": [120,130,110,140,150,160, 90,95,100,105,80,85],
                    "IntraCV": [0.10,0.08,0.12,0.11,0.09,0.07, 0.15,0.14,0.13,0.16,0.18,0.17],
                    "InterCV": [0.12,0.10,0.13,0.12,0.11,0.09, 0.16,0.15,0.14,0.17,0.19,0.18],
                    "PF": [80,82,78,79,83,85, 70,72,68,69,65,67],
                    "Occupancy": [75,78,74,77,79,80, 68,70,66,67,60,62],
                    "QuantValue": [2.1,2.0,2.2,2.3,2.4,2.5, 1.8,1.9,1.7,1.6,1.5,1.4],
                    "LibraryType": ["LT1"]*6 + ["LT2"]*6,
                    "SampleQC": ["pass","pass","pass","pass","pass","pass","pass","pass","fail","pass","pass","fail"]
                })
        elif demo_type == "Genomic":
            demo_path = Path("samples/demo_genomic.csv")
            if demo_path.exists():
                df = pd.read_csv(demo_path)
                st.info("Using bundled genomic demo dataset.")
            else:
                if "demo_notice_shown" not in st.session_state or not st.session_state["demo_notice_shown"]:
                    st.info("Using built-in genomic demo rows (add samples/demo_genomic.csv to customize).")
                    st.session_state["demo_notice_shown"] = True
                df = pd.DataFrame({
                    "SampleID": [f"G{i:03d}" for i in range(1, 11)],
                    "SampleType": ["sample"]*8 + ["positive control","negative control"],
                    "Block": ["X"]*5 + ["Y"]*5,
                    "ReadDepth": [25e6, 28e6, 30e6, 27e6, 29e6, 24e6, 26e6, 23e6, 32e6, 21e6],
                    "MappedReads": [24e6, 27e6, 29e6, 26e6, 28e6, 23e6, 25e6, 22e6, 31e6, 20e6],
                    "DupRate": [0.12,0.11,0.10,0.13,0.09,0.15,0.14,0.16,0.08,0.17],
                    "Coverage": [35,36,34,33,37,32,31,30,38,29],
                    "SampleQC": ["pass","pass","pass","pass","pass","pass","fail","pass","pass","fail"]
                })
    else:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            import pyarrow.parquet as pq, io
            table = pq.read_table(io.BytesIO(uploaded.read()))
            df = table.to_pandas()

    # De-identification confirmation gate
    confirm = st.checkbox("I confirm this file is de-identified (no PHI).")
    if not confirm:
        st.stop()

    try:
        check_phi_columns(df)
        df = standardize_columns(df)
        st.caption("Detected columns: " + ", ".join(df.columns.astype(str)[:20]) + ("…" if len(df.columns) > 20 else ""))
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
            st.image(str(p1), caption="Counts by Group/Block", use_container_width=True)
        if p2.exists():
            st.image(str(p2), caption="External Controls Heatmap", use_container_width=True)

        # --- build PDF & download ---
        pdf_path = outputs / "QC_Report.pdf"
        build_pdf(str(pdf_path), "engine/rules.json", block_summary, ctl_summary, str(p1), str(p2))
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", data=f.read(), file_name="QC_Report.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Error during QC processing: {e}")

st.caption("Research use only • Files processed transiently • No PHI")

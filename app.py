import pandas as pd
from pathlib import Path
from engine.qc import summarize_qc
from engine.plots import boxplot_counts_by_block, heatmap_external_controls
import streamlit as st

st.title("QC Report Builder (De-identified Only)")
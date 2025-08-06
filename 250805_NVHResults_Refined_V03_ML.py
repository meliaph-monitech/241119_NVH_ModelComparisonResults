import os
import zipfile
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Set page layout to wide
st.set_page_config(layout="wide")

# --- Function: Extract ZIP and list CSV files ---
def extract_zip_and_list_files(zip_file):
    csv_files = []
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith(".csv"):  # Include CSV files only
                csv_files.append(file)
    return csv_files

# --- Function: Load robust metadata from GitHub ---
def load_summary_data_from_github():
    url = "https://raw.githubusercontent.com/meliaph-monitech/241119_NVH_ModelComparisonResults/refs/heads/main/241113_NVH_metadata_v03_Robust.csv"
    return pd.read_csv(url)

# --- Function: Load and plot CSV with highlights ---
def load_and_plot_csv_with_highlights(file, summary_df, selected_column):
    raw_data = pd.read_csv(file)

    # Color map including OK-like
    class_color_map = {
        "OK": "red",
        "OK-like": "orange",
        "Hot Melt": "blue",
        "Poor Appearance": "green",
        "Weak Weld": "purple"
    }

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)

    # Plot raw NIR and VIS baseline
    fig.add_trace(go.Scatter(
        x=raw_data.index,
        y=raw_data.iloc[:, 0],
        mode='lines',
        line=dict(color='gray', width=1),
        name='All Data'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=raw_data.index,
        y=raw_data.iloc[:, 1],
        mode='lines',
        line=dict(color='gray', width=1),
        name='All Data',
        showlegend=False
    ), row=2, col=1)

    # Filter metadata for selected file
    file_info = summary_df[summary_df["file"] == os.path.basename(file.name)]
    added_classes = set()
    prediction_order = ["OK", "OK-like", "Hot Melt", "Poor Appearance", "Weak Weld"]

    # Plot highlights
    for pred in prediction_order:
        class_rows = file_info[file_info[selected_column] == pred]

        for _, row in class_rows.iterrows():
            start_idx = int(row["start_index"])
            end_idx = int(row["end_index"])
            prediction = row[selected_column]
            bead_number = row["bead_number"]

            if pd.isna(prediction):
                continue

            color = class_color_map.get(prediction, "black")
            hover_template = f"Bead Number: {bead_number}<br>Class: {prediction}"
            show_legend = prediction not in added_classes

            # NIR trace
            fig.add_trace(go.Scatter(
                x=raw_data.index[start_idx:end_idx + 1],
                y=raw_data.iloc[start_idx:end_idx + 1, 0],
                mode='lines',
                line=dict(color=color, width=1),
                name=f"Class {prediction}" if show_legend else None,
                hovertemplate=hover_template,
                showlegend=show_legend
            ), row=1, col=1)

            # VIS trace
            fig.add_trace(go.Scatter(
                x=raw_data.index[start_idx:end_idx + 1],
                y=raw_data.iloc[start_idx:end_idx + 1, 1],
                mode='lines',
                line=dict(color=color, width=1),
                name=None,
                hovertemplate=hover_template,
                showlegend=False
            ), row=2, col=1)

            added_classes.add(prediction)

    fig.update_layout(
        title=f"Bead-Level NVH Visualization ({selected_column})",
        xaxis_title="Index",
        yaxis_title="NIR Signal",
        xaxis2_title="Index",
        yaxis2_title="VIS Signal",
        height=700,
        showlegend=True
    )

    st.plotly_chart(fig)

# --- Streamlit UI ---
st.title("Bead-Level NVH Data Classification Viewer (Robust Labeling)")

# File uploader for ZIP
uploaded_zip = st.file_uploader("Upload ZIP file containing CSV files", type=["zip"])

if uploaded_zip:
    csv_files = extract_zip_and_list_files(uploaded_zip)

    if csv_files:
        selected_file = st.selectbox("Select CSV File to Plot", csv_files)

        # Load robust metadata
        summary_df = load_summary_data_from_github()

        # Provide choice: refined_label (ground truth) or model predictions
        model_columns = [col for col in summary_df.columns if "_Prediction" in col]
        label_options = ["refined_label"] + model_columns
        selected_column = st.selectbox("Select Label or Model Prediction", label_options)

        # Auto-plot whenever selection changes
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
            with zip_ref.open(selected_file) as file:
                load_and_plot_csv_with_highlights(file, summary_df, selected_column)
    else:
        st.warning("No CSV files found in the uploaded ZIP.")

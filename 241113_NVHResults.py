import os
import zipfile
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Function to extract ZIP file and list all CSV files, including those in subdirectories
def extract_zip_and_list_files(zip_file):
    csv_files = []
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith(".csv"):  # Check if the file is a CSV
                csv_files.append(file)
    return csv_files

# Function to load the summary table
def load_summary_data(file):
    return pd.read_csv(file)

# Function to load and plot CSV data with highlights based on predictions
def load_and_plot_csv_with_highlights(file, summary_df, selected_model):
    raw_data = pd.read_csv(file)

    # Original class-to-color mapping
    class_color_map = {
        0.0: "blue",
        0.1: "red",
        0.2: "green",
        0.3: "purple",
    }

    # Map class labels for legend
    class_labels = {
        0.0: "Hot Melt",
        0.1: "OK",
        0.2: "Poor Appearance",
        0.3: "Weak Weld",
    }

    # Initialize figure
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)

    # Add All Data traces
    fig.add_trace(go.Scatter(
        x=raw_data.index,
        y=raw_data.iloc[:, 0],
        mode='lines',
        line=dict(color='gray', width=1),
        name='All Data',  # Single legend for all unclassified data
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=raw_data.index,
        y=raw_data.iloc[:, 1],
        mode='lines',
        line=dict(color='gray', width=1),
        showlegend=False,  # No additional legend for second column
    ), row=2, col=1)

    # Track added classes to avoid duplicate legend entries
    added_classes = set()

    # Process file_info for classified segments
    file_info = summary_df[summary_df["file"] == os.path.basename(file.name)]
    for idx, row in file_info.iterrows():
        start_idx = int(row["start_index"])
        end_idx = int(row["end_index"])
        prediction = row[selected_model]
        bead_number = row["bead_number"]

        if pd.isna(prediction):
            continue

        color = class_color_map.get(prediction, "black")
        label = class_labels.get(prediction, f"Class {prediction}")
        hover_template = f"Bead Number: {bead_number}<br>Class: {label}"

        # Add trace for first column
        fig.add_trace(go.Scatter(
            x=raw_data.index[start_idx:end_idx + 1],
            y=raw_data.iloc[start_idx:end_idx + 1, 0],
            mode='lines',
            line=dict(color=color, width=1),
            name=label if prediction not in added_classes else None,  # Add to legend only once
            hovertemplate=hover_template,
            showlegend=prediction not in added_classes
        ), row=1, col=1)

        # Add trace for second column (no legend here)
        fig.add_trace(go.Scatter(
            x=raw_data.index[start_idx:end_idx + 1],
            y=raw_data.iloc[start_idx:end_idx + 1, 1],
            mode='lines',
            line=dict(color=color, width=1),
            hovertemplate=hover_template,
            showlegend=False
        ), row=2, col=1)

        added_classes.add(prediction)  # Mark class as added to legend

    # Update layout
    fig.update_layout(
        title="Data Visualization with Predictions and Bead Numbers",
        xaxis_title="Index",
        yaxis_title="NIR Values",
        xaxis2_title="Index",
        yaxis2_title="VIS Values",
        height=700,
        showlegend=True,
        legend=dict(
            traceorder="normal",  # Keep order consistent
            itemsizing='constant',  # Consistent legend item size
        )
    )

    st.plotly_chart(fig)


# Streamlit UI
st.title("CSV File Visualizer")

# File upload for the folder as ZIP
uploaded_zip = st.file_uploader("Upload ZIP file containing CSV files", type=["zip"])

if uploaded_zip:
    # Extract ZIP and list CSV files inside (including files in subdirectories)
    csv_files = extract_zip_and_list_files(uploaded_zip)

    if csv_files:
        selected_file = st.selectbox("Select CSV File to Plot", csv_files)

        uploaded_summary_file = st.file_uploader("Upload Summary CSV File", type=["csv"])

        if uploaded_summary_file:
            summary_df = load_summary_data(uploaded_summary_file)

            model_columns = [col for col in summary_df.columns if "_Prediction" in col]
            selected_model = st.selectbox("Select Model for Coloring", model_columns)

            if st.button("Plot Data"):
                # Extract the CSV file from the zip and load it
                with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                    with zip_ref.open(selected_file) as file:
                        load_and_plot_csv_with_highlights(file, summary_df, selected_model)
    else:
        st.warning("No CSV files found in the ZIP file.")

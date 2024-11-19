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

# Function to update class names in the summary dataframe
def update_class_names_in_summary(summary_df):
    class_name_map = {
        0.0: "Hot Melt",
        1.0: "OK",
        2.0: "Poor Appearance",
        3.0: "Weak Weld"
    }

    # Update the _Prediction columns with new class names
    for col in summary_df.columns:
        if col.endswith("_Prediction"):
            summary_df[col] = summary_df[col].map(class_name_map).fillna(summary_df[col])
    
    return summary_df

# Function to load and plot CSV data with highlights based on predictions
def load_and_plot_csv_with_highlights(file, summary_df, selected_model):
    raw_data = pd.read_csv(file)

    class_color_map = {
        "Hot Melt": "blue",
        "OK": "green",
        "Poor Appearance": "yellow",
        "Weak Weld": "purple"
    }

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)

    # Add all data traces with updated legend name
    fig.add_trace(go.Scatter(
        x=raw_data.index, 
        y=raw_data.iloc[:, 0], 
        mode='lines', 
        line=dict(color='gray', width=1), 
        name='All Data'  # Change legend name for All Data
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=raw_data.index, 
        y=raw_data.iloc[:, 1], 
        mode='lines', 
        line=dict(color='gray', width=1), 
        name='All Data',  # Change legend name for All Data
        showlegend=False  # Suppress duplicate legend entry
    ), row=2, col=1)

    # Reorder the predictions to have "OK" at the top
    file_info = summary_df[summary_df["file"] == os.path.basename(file.name)]
    added_classes = set()  # Track added classes for legends
    prediction_order = ["OK", "Hot Melt", "Poor Appearance", "Weak Weld"]

    for pred in prediction_order:
        # For each class in the desired order
        class_rows = file_info[file_info[selected_model] == pred]

        for idx, row in class_rows.iterrows():
            start_idx = int(row["start_index"])
            end_idx = int(row["end_index"])
            prediction = row[selected_model]
            bead_number = row["bead_number"]

            if pd.isna(prediction):
                continue

            color = class_color_map.get(prediction, "black")

            hover_template = f"Bead Number: {bead_number}<br>Class: {prediction}"

            show_legend = prediction not in added_classes  # Only show legend for first appearance

            fig.add_trace(go.Scatter(
                x=raw_data.index[start_idx:end_idx + 1],
                y=raw_data.iloc[start_idx:end_idx + 1, 0],
                mode='lines',
                line=dict(color=color, width=1),
                name=f"Class {prediction}" if show_legend else None,  # Add to legend if not added
                hovertemplate=hover_template,
                showlegend=show_legend  # Suppress additional legend entries
            ), row=1, col=1)

            fig.add_trace(go.Scatter(
                x=raw_data.index[start_idx:end_idx + 1],
                y=raw_data.iloc[start_idx:end_idx + 1, 1],
                mode='lines',
                line=dict(color=color, width=1),
                name=None,  # No duplicate legend entries for the second column
                hovertemplate=hover_template,
                showlegend=False  # Suppress legend
            ), row=2, col=1)

            added_classes.add(prediction)  # Mark this class as added

    fig.update_layout(
        title="Data Visualization with Predictions and Bead Numbers",
        xaxis_title="Index",
        yaxis_title="NIR Values",
        xaxis2_title="Index",
        yaxis2_title="VIS Values",
        height=700,
        showlegend=True
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

            # Update class names in the summary dataframe
            summary_df = update_class_names_in_summary(summary_df)

            model_columns = [col for col in summary_df.columns if "_Prediction" in col]
            selected_model = st.selectbox("Select Model for Coloring", model_columns)

            if st.button("Plot Data"):
                # Extract the CSV file from the zip and load it
                with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                    with zip_ref.open(selected_file) as file:
                        load_and_plot_csv_with_highlights(file, summary_df, selected_model)
    else:
        st.warning("No CSV files found in the ZIP file.")

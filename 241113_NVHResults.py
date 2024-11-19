import os
import zipfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import io

# Function to extract ZIP file and list CSV files
def extract_zip_and_list_files(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall("extracted_folder")  # Extract to a directory called "extracted_folder"
        return [f for f in os.listdir("extracted_folder") if f.endswith(".csv")]

# Function to load the summary table
def load_summary_data(file):
    return pd.read_csv(file)

# Function to load and plot CSV data with highlights based on predictions
def load_and_plot_csv_with_highlights(file_name, summary_df, selected_model):
    if not os.path.exists(file_name):
        st.error(f"File '{file_name}' not found.")
        return

    raw_data = pd.read_csv(file_name)

    class_color_map = {
        0.0: "blue",
        1.0: "red",
        2.0: "green",
        3.0: "purple",
        4.0: "orange"
    }

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)

    fig.add_trace(go.Scatter(x=raw_data.index, y=raw_data.iloc[:, 0], mode='lines', line=dict(color='gray'), name='All Data (First Column)'), row=1, col=1)
    fig.add_trace(go.Scatter(x=raw_data.index, y=raw_data.iloc[:, 1], mode='lines', line=dict(color='gray'), name='All Data (Second Column)'), row=2, col=1)

    file_info = summary_df[summary_df["file"] == os.path.basename(file_name)]
    added_classes = set()

    for idx, row in file_info.iterrows():
        start_idx = int(row["start_index"])
        end_idx = int(row["end_index"])
        prediction = row[selected_model]

        if pd.isna(prediction):
            continue

        color = class_color_map.get(prediction, "black")
        linestyle = 'dash' if row["is_test"] else 'solid'

        fig.add_trace(go.Scatter(
            x=raw_data.index[start_idx:end_idx + 1],
            y=raw_data.iloc[start_idx:end_idx + 1, 0],
            mode='lines',
            line=dict(color=color, dash=linestyle),
            name=f"Class {prediction}" if prediction not in added_classes else None
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=raw_data.index[start_idx:end_idx + 1],
            y=raw_data.iloc[start_idx:end_idx + 1, 1],
            mode='lines',
            line=dict(color=color, dash=linestyle),
            name=f"Class {prediction}" if prediction not in added_classes else None
        ), row=2, col=1)

        added_classes.add(prediction)

    fig.update_layout(
        title="Data Visualization with Predictions",
        xaxis_title="Index",
        yaxis_title="First Column Values",
        xaxis2_title="Index",
        yaxis2_title="Second Column Values",
        height=700,
        showlegend=True
    )

    st.plotly_chart(fig)

# Streamlit UI
st.title("CSV File Visualizer")

# File upload for the folder as ZIP
uploaded_zip = st.file_uploader("Upload ZIP file containing CSV files", type=["zip"])

if uploaded_zip:
    # Extract ZIP and list CSV files inside
    csv_files = extract_zip_and_list_files(uploaded_zip)

    if csv_files:
        selected_file = st.selectbox("Select CSV File to Plot", csv_files)

        uploaded_summary_file = st.file_uploader("Upload Summary CSV File", type=["csv"])

        if uploaded_summary_file:
            summary_df = load_summary_data(uploaded_summary_file)

            model_columns = [col for col in summary_df.columns if "_Prediction" in col]
            selected_model = st.selectbox("Select Model for Coloring", model_columns)

            if st.button("Plot Data"):
                file_path = os.path.join("extracted_folder", selected_file)
                load_and_plot_csv_with_highlights(file_path, summary_df, selected_model)
    else:
        st.warning("No CSV files found in the ZIP file.")

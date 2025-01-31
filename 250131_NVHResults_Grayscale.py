import os
import zipfile
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(layout="wide")

def extract_zip_and_list_files(zip_file):
    csv_files = []
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith(".csv"):
                csv_files.append(file)
    return csv_files

def load_summary_data_from_github():
    url = "https://raw.githubusercontent.com/meliaph-monitech/NVH_ModelComparisonResults/refs/heads/main/241113_NVH_metadata.csv"
    return pd.read_csv(url)

def update_class_names_in_summary(summary_df):
    class_name_map = {
        0.0: "Hot Melt",
        1.0: "OK",
        2.0: "Poor Appearance",
        3.0: "Weak Weld"
    }
    for col in summary_df.columns:
        if col.endswith("_Prediction"):
            summary_df[col] = summary_df[col].map(class_name_map).fillna(summary_df[col])
    return summary_df

def load_and_plot_csv(file, summary_df, selected_model, show_colors):
    raw_data = pd.read_csv(file)
    class_color_map = {
        "Hot Melt": "blue",
        "OK": "red",
        "Poor Appearance": "green",
        "Weak Weld": "purple"
    }
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    
    # Default gray lines
    fig.add_trace(go.Scatter(x=raw_data.index, y=raw_data.iloc[:, 0], mode='lines', line=dict(color='gray', width=1), name='All Data'), row=1, col=1)
    fig.add_trace(go.Scatter(x=raw_data.index, y=raw_data.iloc[:, 1], mode='lines', line=dict(color='gray', width=1), name='All Data', showlegend=False), row=2, col=1)
    
    if show_colors:
        file_info = summary_df[summary_df["file"] == os.path.basename(file.name)]
        added_classes = set()
        prediction_order = ["OK", "Hot Melt", "Poor Appearance", "Weak Weld"]
        
        for pred in prediction_order:
            class_rows = file_info[file_info[selected_model] == pred]
            for _, row in class_rows.iterrows():
                start_idx, end_idx = int(row["start_index"]), int(row["end_index"])
                prediction, bead_number = row[selected_model], row["bead_number"]
                if pd.isna(prediction):
                    continue
                color = class_color_map.get(prediction, "black")
                hover_template = f"Bead Number: {bead_number}<br>Class: {prediction}"
                show_legend = prediction not in added_classes
                
                fig.add_trace(go.Scatter(x=raw_data.index[start_idx:end_idx + 1], y=raw_data.iloc[start_idx:end_idx + 1, 0],
                                         mode='lines', line=dict(color=color, width=1), name=f"Class {prediction}" if show_legend else None,
                                         hovertemplate=hover_template, showlegend=show_legend), row=1, col=1)
                
                fig.add_trace(go.Scatter(x=raw_data.index[start_idx:end_idx + 1], y=raw_data.iloc[start_idx:end_idx + 1, 1],
                                         mode='lines', line=dict(color=color, width=1), name=None, hovertemplate=hover_template, showlegend=False), row=2, col=1)
                
                added_classes.add(prediction)
    
    fig.update_layout(title="Data Visualization", xaxis_title="Index", yaxis_title="NIR Values", xaxis2_title="Index", yaxis2_title="VIS Values", height=700, showlegend=True)
    st.plotly_chart(fig)

st.title("NVH Data Classification Model Training Results")
uploaded_zip = st.file_uploader("Upload ZIP file containing CSV files", type=["zip"])

if uploaded_zip:
    csv_files = extract_zip_and_list_files(uploaded_zip)
    if csv_files:
        selected_file = st.selectbox("Select CSV File to Plot", csv_files)
        summary_df = update_class_names_in_summary(load_summary_data_from_github())
        model_columns = [col for col in summary_df.columns if "_Prediction" in col]
        selected_model = st.selectbox("Select Model for Coloring", model_columns)
        show_colors = st.toggle("Show Color Coding", value=False)
        
        if st.button("Plot Data"):
            with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                with zip_ref.open(selected_file) as file:
                    load_and_plot_csv(file, summary_df, selected_model, show_colors)
    else:
        st.warning("No CSV files found in the ZIP file.")

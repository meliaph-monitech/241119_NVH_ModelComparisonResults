import os
import pandas as pd
import plotly.graph_objs as go
import streamlit as st

# Function to load the summary table
def load_summary_data(file):
    return pd.read_csv(file)

# Function to load and plot CSV data with highlights based on predictions
def load_and_plot_csv_with_highlights(file_name, summary_df, selected_model):
    raw_data = pd.read_csv(file_name)

    # Color mapping for predictions
    class_color_map = {
        0.0: "blue",
        1.0: "red",
        2.0: "green",
        3.0: "purple",
        4.0: "orange"
    }

    # Create a Plotly figure
    fig = go.Figure()

    # Plot all data in gray
    fig.add_trace(go.Scatter(x=raw_data.index, y=raw_data.iloc[:, 0],
                             mode='lines', line=dict(color='gray'),
                             name='All Data - First Column'))
    fig.add_trace(go.Scatter(x=raw_data.index, y=raw_data.iloc[:, 1],
                             mode='lines', line=dict(color='gray'),
                             name='All Data - Second Column'))

    # Highlight bead data based on the selected model's predictions
    file_info = summary_df[summary_df["file"] == os.path.basename(file_name)]
    
    # Keep track of added classes for legend
    added_classes = set()
    
    # Iterate through the rows for each bead
    for idx, row in file_info.iterrows():
        start_idx = int(row["start_index"])
        end_idx = int(row["end_index"])
        prediction = row[selected_model]  # Use predictions for coloring
        
        if pd.isna(prediction):
            continue
        
        color = class_color_map.get(prediction, "black")

        # Add traces for the highlighted data
        if prediction not in added_classes:
            fig.add_trace(go.Scatter(x=range(start_idx, end_idx + 1),
                                     y=raw_data.iloc[start_idx:end_idx + 1, 0],
                                     mode='lines', line=dict(color=color),
                                     name=f'Class {prediction} - First Column'))
            fig.add_trace(go.Scatter(x=range(start_idx, end_idx + 1),
                                     y=raw_data.iloc[start_idx:end_idx + 1, 1],
                                     mode='lines', line=dict(color=color),
                                     name=f'Class {prediction} - Second Column'))
            added_classes.add(prediction)

    # Update layout
    fig.update_layout(title='Highlighted Data by Class',
                      xaxis_title='Index',
                      yaxis_title='Values',
                      showlegend=True)

    st.plotly_chart(fig)

# Streamlit app
def main():
    st.title("Bead Data Visualization")

    # File uploader for summary CSV
    summary_file = st.file_uploader("Upload Summary CSV", type="csv")
    
    if summary_file:
        summary_df = load_summary_data(summary_file)
        
        # Input for data directory
        data_directory = st.text_input("Enter the directory containing CSV files:")

        if data_directory:
            # Find all CSV files inside the specified directory
            csv_files = [os.path.join(data_directory, file) for file in os.listdir(data_directory) if file.endswith('.csv')]
            
            # Dropdown to select CSV file
            selected_file = st.selectbox("Select CSV File", csv_files)

            # Dropdown to select model
            model_columns = [col for col in summary_df.columns if "_Prediction" in col]
            selected_model = st.selectbox("Select Model", model_columns)

            # Plot button
            if st.button("Plot Data"):
                load_and_plot_csv_with_highlights(selected_file, summary_df, selected_model)

if __name__ == "__main__":
    main()

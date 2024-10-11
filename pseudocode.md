# Pseudocode for Data Analysis Application using Streamlit

## 1. **Import Dependencies**:
   - Import required libraries:
     - `streamlit as st` for user interface development.
     - `pandas as pd` and `numpy as np` for data manipulation.
     - `matplotlib.pyplot as plt` for creating visualizations.
     - `matplotlib.colors` and `matplotlib.ticker` for customization of the visualizations.
     - `datetime`, `pytz`, `io`, `base64`, `yaml` for specific functionalities related to time management, data export, and configuration loading.

## 2. **Load Configuration**:
   - Function: `read_config(config_file='config.yaml')`
     - Load the configuration settings from an external YAML file.
     - Return a dictionary containing all configuration values.
     - Handle cases where the file is missing or contains errors.

## 3. **Define Functions**:

   a. **`load_and_process_data(uploaded_file)`**:
   - Load the Excel file (`.xlsx`) provided by the user, skipping rows as specified in the configuration (`skip_rows`).
   - If specified, remove the first column (`remove_first_column`).
   - Check if all required columns, such as `'DIFERENÇA (%)'`, are present; raise an error if any are missing.
   - Convert the `'DATA'` column to datetime format to facilitate date filtering.
   - Return the processed DataFrame or an error message if data issues are detected.

   b. **`find_correct_columns(df, config)`**:
   - Identify the correct indices for the required columns (`PREVISTO (KG)`, `REALIZADO (KG)`, `DIFERENÇA (%)`).
   - Extract indices based on column names from the configuration file.
   - Return a dictionary with column indices, raising an error if the structure does not match expectations.

   c. **`calculate_weighted_average_with_weights(df, pesos_relativos, config)`**:
   - Convert the necessary columns to numeric to handle missing or invalid values (`errors='coerce'`).
   - Calculate the absolute value of `'DIFERENÇA (%)'`.
   - Map relative weights (`PESO RELATIVO`) to each `TIPO` using user inputs.
   - Calculate the adjusted planned quantity (`PESO AJUSTADO`) as `PREVISTO (KG) * PESO RELATIVO`.
   - Group by `'COD. BATIDA'` to aggregate the adjusted planned quantities and contributions.
   - Calculate the weighted average for each group by dividing the total contributions by total adjusted quantities.
   - Return a DataFrame containing the weighted averages, ensuring all calculations are accurate.

   d. **`remove_outliers_from_df(df, column)`**:
   - Calculate the interquartile range (IQR) using Q1 and Q3.
   - Determine the upper bound for outliers as `Q3 + 1.5 * IQR`.
   - Filter out rows where the value in the specified column exceeds this upper bound.
   - Return the filtered DataFrame.

   e. **`filter_data(df, operadores, alimentos, dietas, start_date, end_date)`**:
   - Convert `start_date` and `end_date` to datetime format.
   - Filter data based on the provided date range.
   - Further filter the data based on the user-selected operators (`OPERADOR`), food types (`ALIMENTO`), and diets (`NOME`).
   - Return the filtered DataFrame, ensuring no data is excluded incorrectly.

   f. **`create_histogram(df, start_date, end_date, remove_outliers, pesos_relativos)`**:
   - If `remove_outliers` is `True`, call `remove_outliers_from_df()` on the `'MÉDIA PONDERADA (%)'` column.
   - Use `matplotlib` to create a histogram of `'MÉDIA PONDERADA (%)'`.
   - Calculate histogram bins using the Freedman-Diaconis rule for optimal visualization.
   - Apply a color scheme to the bars:
     - Color bars red for values greater than or equal to the tolerance threshold (from configuration), with increasing intensity based on proximity.
     - Color bars green for values below the threshold.
   - Set labels for axes and add a vertical dashed line to indicate the tolerance limit.
   - Add footer information, including:
     - Analysis period (`start_date` to `end_date`).
     - Total number of batches analyzed.
     - Generation timestamp using Brasília time.
   - Display relative weights (`PESO RELATIVO`) for different food types on the right-hand side of the histogram.
   - Return the figure.

   g. **`save_histogram_as_image(fig)`**:
   - Save the histogram figure as a PNG file using a `BytesIO` buffer.
   - Encode the image as Base64 and generate an HTML link for downloading the image.
   - Return the download link for Streamlit display.

   h. **`save_statistics_as_csv(stats_df)`**:
   - Save a DataFrame containing calculated statistics as a CSV file.
   - Encode the CSV as Base64 and generate an HTML link for downloading.
   - Return the download link.

## 4. **Create Statistics Dataframe (`create_statistics_dataframe(weighted_average_df, remove_outliers=False)`)**:
   - Create a copy of the DataFrame to avoid modifying the original data.
   - Calculate statistical measures like mean, median, and counts of differences in various ranges.
   - If `remove_outliers` is `True`, filter out outliers before calculating statistics.
   - Return a DataFrame containing the main statistics.

## 5. **Main Function (`main()`)**:

   - Set up the Streamlit page configuration with a title and a "wide" layout.
   - Create two main columns for the user interface:
     - **Settings Column**:
       - Allow users to upload an Excel file (`.xlsx`).
       - Call `load_and_process_data()` to load and verify the data.
       - If data loads successfully:
         - Display sliders for setting relative weights (`PESO RELATIVO`) for each `TIPO`.
         - Provide multiselect options for filtering by `OPERADOR`, `ALIMENTO`, and `NOME`.
         - Allow date range selection for analysis.
         - Add a checkbox to remove outliers before analysis.
         - Include a "Generate" button to initiate the analysis.
     - **Results Column**:
       - If the "Generate" button is clicked:
         - Filter the data using `filter_data()` based on user selections.
         - If the filtered dataset is not empty:
           - Calculate weighted averages using `calculate_weighted_average_with_weights()`.
           - Create a histogram using `create_histogram()`.
           - Display the histogram using `st.pyplot()`.
           - Offer a download link for the histogram (`save_histogram_as_image()`).
           - Generate a DataFrame of main statistics using `create_statistics_dataframe()`.
           - Provide the option to download the statistics (`save_statistics_as_csv()`).
           - Display a message indicating outliers were removed, if applicable.

## 6. **Entry Point**:
   - Ensure the `main()` function is called when the script runs:
   ```python
   if __name__ == "__main__":
       main()
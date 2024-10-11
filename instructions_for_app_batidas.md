## Instruction Prompt for the Python Program

Write a Python program using the Streamlit framework to create a data analysis web app for visualizing batch-level metrics using histograms. The program should meet the following updated requirements:

### Key Requirements:

1. **Dependencies**:
   - Use `pandas`, `numpy`, `matplotlib`, `streamlit`, and `pyyaml`.
   - Import additional libraries such as `datetime`, `io`, `base64`, and `pytz` for specific functionalities.
   - Use `matplotlib.colors` and `matplotlib.ticker` for advanced visualization formatting.

2. **Configuration File Management**:
   - The configuration settings should be managed through an external YAML file (`config.yaml`).
   - The configuration file must include:
     - **Excel Column Mapping** (`excel_columns`): Column names used in the uploaded dataset.
     - **Analysis Settings** (`analysis`): Default weights, tolerance thresholds, outlier thresholds, and row skipping instructions.
     - **User Interface Settings** (`ui`): Labels, titles, and user options for the Streamlit interface.
     - **Visualization Settings** (`visualization`): Settings for histogram size, grid style, colors, legends, and layout adjustments.

3. **Load and Process Data**:
   - Function: `load_and_process_data(uploaded_file)`
     - Load an Excel file (`.xlsx`), skipping rows as defined in the YAML file.
     - Remove the first column if specified in the configuration.
     - Ensure required columns are present, such as 'DIFERENÇA (%)'.
     - Convert 'DATA' to datetime format for filtering.
     - Return the processed DataFrame or display an error message if necessary.

4. **Find Correct Columns**:
   - Function: `find_correct_columns(df, config)`
     - Identify the indices of important columns such as `PREVISTO (KG)` and `REALIZADO (KG)`.
     - Ensure that dependent columns (`REALIZADO (KG)` and `DIFERENÇA (%)`) are found correctly based on configuration.

5. **Weighted Average Calculation with Relative Weights**:
   - Function: `calculate_weighted_average_with_weights(df, pesos_relativos, config)`
     - Convert necessary columns to numeric format and calculate the absolute value of the percentage difference.
     - Assign relative weights to each type of food (`TIPO`) using user inputs.
     - Calculate the adjusted planned quantity (`PESO AJUSTADO`).
     - Group data by 'COD. BATIDA' and calculate the weighted average of the differences.
     - Return a DataFrame containing the weighted averages.

6. **Outlier Removal**:
   - Function: `remove_outliers_from_df(df, column)`
     - Use the IQR method to calculate and exclude values above a calculated upper bound.
     - Return the filtered DataFrame.

7. **Data Filtering**:
   - Function: `filter_data(df, operadores, alimentos, dietas, start_date, end_date)`
     - Filter the DataFrame based on user inputs: date range, operators (`OPERADOR`), food types (`ALIMENTO`), and diets (`NOME`).
     - Return the filtered DataFrame.

8. **Histogram Creation**:
   - Function: `create_histogram(df, start_date, end_date, remove_outliers, pesos_relativos)`
     - Use `matplotlib` to create a histogram of 'MÉDIA PONDERADA (%)'.
     - Apply outlier removal based on user preference.
     - Color histogram bars based on their value:
       - Values >= tolerance threshold are colored red.
       - Values < tolerance are colored green.
     - Set labels, grid lines, and add a vertical dashed line representing the tolerance threshold.
     - Add footer details for analysis period, total batches, and generation timestamp.
     - Display relative weights for each food type on the right side of the histogram.
     - Return the figure.

9. **Save Histogram and Statistics**:
   - Function: `save_histogram_as_image(fig)`
     - Save the histogram as a PNG and provide a link to download it.

   - Function: `save_statistics_as_csv(stats_df)`
     - Save statistics as a CSV and provide a link for download.

10. **Streamlit User Interface**:
    - Function: `main()`
      - Set up the page with appropriate titles and a "wide" layout.
      - Create two columns for analysis settings and displaying results.
      - Include a file uploader for Excel files, allowing only `.xlsx` files.
      - Add analysis parameters such as:
        - **Relative Weights**: Sliders for setting weights for `TIPO`.
        - **Filtering**: Multiselect inputs for operators, food types, diets, and a date range selection.
        - **Outlier Removal**: Checkbox to remove outliers from analysis.
      - Add a "Generate" button to start the analysis.
      - Upon clicking "Generate":
        - Load and filter data.
        - Calculate the weighted average.
        - Generate and display the histogram.
        - Provide options to download the histogram (PNG) and the statistics (CSV).
        - Display tables for analysis results and relative weights.

11. **Timezone Setting**:
    - All generation timestamps must be displayed in the Brasília time zone using `pytz`.

12. **Function Calls**:
    - Ensure the `main()` function is called using:
      ```python
      if __name__ == "__main__":
          main()
      ```

### Running the Application

To run the Streamlit app, use the following command:

```bash
streamlit run batidas.py

```

## GitHub Commands

```bash
git status
git add batidas.py instructions_for_app_batidas.md requirements.txt pseudocode.md config.yaml
git commit -m "Updated version of batidas app - improvements in graph, statistics table, and added config.yaml"
git push origin main
```

## Virtual Environment Activation

```bash
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Remember to deactivate the virtual environment when you're done:

```bash
deactivate
``` 
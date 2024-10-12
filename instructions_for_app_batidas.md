## Instructions for the Data Analysis Application with Streamlit

Write a Python program using the **Streamlit** framework to create a web-based data analysis application that visualizes batch metrics using histograms. The program should follow the requirements described below:

### **Main Requirements**:

1. **Dependencies**:
   - Use the libraries `pandas`, `numpy`, `matplotlib`, `streamlit`, and `pyyaml`.
   - Import additional libraries such as `datetime`, `io`, `base64`, and `pytz` for specific functionalities.
   - Use `matplotlib.colors` and `matplotlib.ticker` for advanced visualization customization.

2. **Configuration Management via YAML**:
   - The configuration file should be managed through an external YAML file (`config.yaml`).
   - The file should include:
     - **Excel Column Mapping** (`excel_columns`): Names of the columns used in the loaded dataset.
     - **Analysis Settings** (`analysis`): Default weights, tolerance thresholds, outlier handling, and data processing instructions.
     - **User Interface Settings** (`ui`): Titles, labels, and configuration options for the interface.
     - **Visualization Settings** (`visualization`): Histogram size, grid style, colors, legends, and layout adjustments.

3. **Function to Load and Process Data**:
   - Function: `load_and_process_data(uploaded_file)`
     - Loads an Excel file (`.xlsx`), skipping lines as configured in YAML.
     - Removes the first column if configured.
     - Ensures that essential columns, such as 'DIFERENÇA (%)', are present.
     - Converts the 'DATA' column to datetime format for data filtering.
     - Returns a processed Pandas DataFrame or displays an error message if necessary.

4. **Column Identification**:
   - Function: `find_correct_columns(df, config)`
     - Identifies the indices of important columns, such as `PREVISTO (KG)` and `REALIZADO (KG)`, based on the configuration.

5. **Calculation of Weighted Average with Relative Weights**:
   - Function: `calculate_weighted_average_with_weights(df, pesos_relativos, config)`
     - Converts columns to numeric format and calculates the absolute value of the percentage difference.
     - Applies relative weights to each food type (`TIPO`) as provided by the user.
     - Calculates the adjusted planned amount (`PESO AJUSTADO`).
     - Groups the data by 'COD. BATIDA' and calculates the weighted average of the differences.
     - Returns a DataFrame containing the weighted averages.

6. **Outlier Removal**:
   - Function: `remove_outliers_from_df(df, column)`
     - Uses the IQR method to calculate and exclude values outside a calculated upper limit.
     - Returns the filtered DataFrame.

7. **Data Filtering**:
   - Function: `filter_data(df, operadores, alimentos, dietas, start_date, end_date)`
     - Filters the DataFrame based on user inputs: date range, operators (`OPERADOR`), food types (`ALIMENTO`), and diets (`NOME`).
     - Returns the filtered DataFrame.

8. **Histogram Creation**:
   - Function: `create_histogram(df, start_date, end_date, remove_outliers, pesos_relativos)`
     - Uses `matplotlib` to create a histogram of 'MÉDIA PONDERADA (%)'.
     - Applies outlier removal based on user preference.
     - Colors the histogram bars based on the values:
       - Values >= tolerance threshold are colored red.
       - Values < tolerance are colored green.
     - Configures labels, gridlines, and adds a dashed vertical line representing the tolerance threshold.
     - Adds footer details about the analysis period, total batches, and a timestamp.
     - Displays relative weights for each food type on the right side of the histogram.
     - Returns the generated figure.

9. **Saving Histograms and Statistics**:
   - Function: `save_histogram_as_image(fig)`
     - Saves the histogram as a PNG image and generates a download link.

   - Function: `save_statistics_as_csv(stats_df)`
     - Saves the statistics as a CSV file and generates a download link.

10. **User Interface with Streamlit**:
    - Function: `main()`
      - Sets up the page with an appropriate title and "wide" layout.
      - Creates two columns for analysis parameters and results display.
      - Includes a file uploader for Excel files, allowing only `.xlsx`.
      - Adds analysis parameters, such as:
        - **Relative Weights**: Sliders to adjust weights for `TIPO`.
        - **Filtering**: Multiselect inputs for operators, food types, diets, and date range selection.
        - **Outlier Removal**: Checkbox to remove outliers from the analysis.
      - Adds a "Generate" button to start the analysis.
      - Upon clicking "Generate":
        - Loads and filters the data.
        - Calculates the weighted average.
        - Generates and displays the histogram.
        - Provides options to download the histogram (PNG) and the statistics (CSV).
        - Displays tables with results and relative weights.

11. **Timezone Configuration**:
    - All generated timestamps must be displayed in the Brasília timezone using `pytz`.

12. **Function Calls**:
    - Ensure that the `main()` function is called using:
      ```python
      if __name__ == "__main__":
          main()
      ```

### **Running the Application**:

To run the Streamlit application, use the following command:

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
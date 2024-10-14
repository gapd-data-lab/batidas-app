## Instructions for the Data Analysis Application with Streamlit

Develop a Python program using the **Streamlit** framework to create a sophisticated web-based data analysis application that visualizes batch metrics using histograms. The program should adhere to the specifications detailed below:

### **Primary Requirements**:

1. **Dependencies**:

   - Utilize the libraries `pandas`, `numpy`, `matplotlib`, `streamlit`, and `pyyaml`.
   - Include additional libraries such as `datetime`, `io`, `base64`, and `pytz` for specific functionalities.
   - Employ `matplotlib.colors` and `matplotlib.ticker` for advanced customization of visualizations.

2. **Configuration Management via YAML**:

   - Configuration settings should be managed through an external YAML file (`config.yaml`).
   - The YAML file must include:
     - **Excel Column Mapping** (`excel_columns`): Specifies the names of the columns used in the dataset, including information on **duplicated columns** (`PREVISTO (KG).1` and `REALIZADO (KG).1`) which require specialized handling to ensure clarity during analysis.
     - **Analysis Settings** (`analysis`): Defines default weights, tolerance thresholds, outlier management, and data processing instructions, including strategies for handling **missing values (NaN)** to maintain consistency in data analysis.
     - **User Interface Settings** (`ui`): Configures titles, labels, and other options related to the user interface.
     - **Visualization Settings** (`visualization`): Specifies settings such as histogram size, grid style, colors, legends, and layout configurations.

3. **Function to Load and Process Data**:

   - Function: `load_and_process_data(uploaded_file)`
     - Loads an Excel file (`.xlsx`), skipping rows as configured in YAML.
     - Removes the first column if specified in the configuration.
     - Ensures that essential columns, such as 'DIFERENÇA (%)', are present.
     - Converts the 'DATA' column to datetime format for subsequent filtering.
     - **Validates duplicated columns** (`PREVISTO (KG).1`, `REALIZADO (KG).1`) to ensure consistency across data entries.
     - Returns a processed Pandas DataFrame or displays an error message if validation fails.

4. **Column Identification**:

   - Function: `find_correct_columns(df, config)`
     - Identifies the indices of critical columns, such as `PREVISTO (KG)` and `REALIZADO (KG)`, based on the configuration file.

5. **Calculation of Weighted Average with Relative Weights**:

   - Function: `calculate_weighted_average_with_weights(df, pesos_relativos, config)`
     - Converts specified columns to numeric format and calculates the absolute value of the percentage difference.
     - Applies relative weights to each food type (`TIPO`) based on user input.
     - Computes the adjusted planned amount (`PESO AJUSTADO`).
     - Groups the data by 'COD. BATIDA' and calculates the weighted average of differences.
     - **Implements robust error messages** for cases where essential columns are missing or data cannot be processed.
     - Returns a DataFrame containing the computed weighted averages.

6. **Outlier Removal**:

   - Function: `remove_outliers_from_df(df, column)`
     - Utilizes the Interquartile Range (IQR) method to identify and remove values outside a calculated threshold.
     - Returns the filtered DataFrame.

7. **Data Filtering**:

   - Function: `filter_data(df, operadores, alimentos, dietas, start_date, end_date)`
     - Filters the DataFrame based on user inputs, including date range, operators (`OPERADOR`), food types (`ALIMENTO`), and diets (`NOME`).
     - Returns the filtered DataFrame.

8. **Histogram Creation**:

   - Function: `create_histogram(df, start_date, end_date, remove_outliers, pesos_relativos)`
     - Utilizes `matplotlib` to generate a histogram of 'MÉDIA PONDERADA (%)'.
     - Applies outlier removal if specified by the user.
     - Colors histogram bars based on threshold values:
       - Values >= tolerance threshold are colored red.
       - Values < tolerance are colored green.
     - Configures labels, gridlines, and includes a dashed vertical line indicating the tolerance threshold.
     - Adds footer details summarizing the analysis period, total batches, and a timestamp.
     - Displays relative weights for each food type on the right side of the histogram.
     - **Adds a legend** that provides a clear explanation of the color coding used in the histogram.
     - Returns the generated figure.

9. **Saving Histograms and Statistics**:

   - Function: `save_histogram_as_image(fig)`
     - Saves the histogram as a PNG image and generates a download link.

   - Function: `save_statistics_as_csv(stats_df)`
     - Saves the statistical analysis as a CSV file and generates a download link.
     - **Allows users to choose alternative file formats** (e.g., PDF for visualizations and Excel for tabular data) to enhance accessibility.

10. **User Interface with Streamlit**:

    - Function: `main()`
      - Configures the page with an appropriate title and "wide" layout.
      - Creates two columns for parameter input and results display.
      - Includes a file uploader that accepts only `.xlsx` files.
      - Adds configuration options such as:
        - **Relative Weights**: Sliders to adjust weights for `TIPO`. Consider including **two sliders for each food type**: one for default weight and another for a finer adjustment factor to provide more granular control.
        - **Filtering**: Multiselect inputs for operators, food types, diets, and date range selection. Consider configuring **default start and end dates** in the YAML file to streamline user interaction.
        - **Outlier Removal**: Checkbox to enable or disable the removal of outliers during analysis.
      - Adds a "Generate" button to initiate the analysis.
      - Upon clicking "Generate":
        - Loads and filters the data.
        - Calculates the weighted average.
        - Generates and displays the histogram.
        - Provides options to download both the histogram (PNG) and the statistics (CSV).
        - Displays tables with results and relative weights.

11. **Timezone Configuration**:

    - Ensure that all generated timestamps are displayed in the Brasília timezone using `pytz`.

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
git add batidas.py instructions_for_app_batidas.md requirements.txt pseudocode.md config.yaml requirements.md formula_calculo.tex batidas_versao_1_0.py config_versao_1_0.yaml
git commit -m "Updated version of batidas app and in config.yaml"
git push origin main
```

## Virtual Environment Activation

```bash
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Remember to deactivate the virtual environment when finished:

```bash
deactivate
```
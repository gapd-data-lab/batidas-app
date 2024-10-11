Write a Python program using the Streamlit framework to create a data analysis web app for visualizing batch-level metrics using histograms. The program should meet the following requirements:

### Key Requirements:

1. **Dependencies**:
   - Use `pandas`, `numpy`, `matplotlib`, and `streamlit`.
   - Import additional libraries such as `datetime`, `io`, `base64`, and `pytz` for specific functionalities.

2. **Load and Process Data**:
   - Function: `load_and_process_data(uploaded_file)`
     - Load an Excel file (`.xlsx`), skipping the first two rows (metadata).
     - Remove the first column since it is irrelevant.
     - Ensure 'DIFERENÇA (%)' is present and convert its values to numeric.
     - Convert 'DATA' to datetime format for filtering.
     - Return the processed DataFrame.

3. **Weighted Average Calculation with Relative Weights**:
   - Function: `calculate_weighted_average_with_weights(df, pesos_relativos)`
     - Access columns `PREVISTO (KG)`, `REALIZADO (KG)`, and `DIFERENÇA (%)` by their positions.
     - Calculate the absolute value of the percentage difference.
     - Assign relative weights to each type of food (`TIPO`) using user inputs.
     - Calculate the adjusted planned quantity (`PESO AJUSTADO`).
     - Group data by 'COD. BATIDA' and calculate the weighted average of the differences:
       - Multiply the adjusted planned quantity by the percentage difference to determine contributions.
       - Divide the sum of contributions by total adjusted planned quantity for each batch.
     - Return a DataFrame containing the weighted averages.

4. **Outlier Removal**:
   - Function: `remove_outliers_from_df(df, column)`
     - Use the IQR method to calculate and exclude values above a calculated upper bound.
     - Return the filtered DataFrame.

5. **Data Filtering**:
   - Function: `filter_data(df, operadores, alimentos, dietas, start_date, end_date)`
     - Filter the DataFrame based on date range, operators (`OPERADOR`), food types (`ALIMENTO`), and diets (`NOME`).
     - Return the filtered DataFrame.

6. **Histogram Creation**:
   - Function: `create_histogram(df, title, start_date, end_date, remove_outliers=False)`
     - Use `matplotlib` to create a histogram of 'MÉDIA PONDERADA (%)'.
     - Optionally apply outlier removal.
     - Color bars based on value:
       - Values >= 3% are red, with increasing intensity.
       - Values < 3% are green, based on proximity to zero.
     - Set labels, grid lines, and a vertical dashed line at 3%.
     - Add footer details for analysis period, total batches, and generation timestamp.
     - Return the figure.

7. **Save Histogram and Statistics**:
   - Function: `save_histogram_as_image(fig)`
     - Save the histogram as a PNG and provide a link to download it.

   - Function: `save_statistics_as_csv(stats_df)`
     - Save statistics as a CSV and provide a link for download.

8. **Streamlit User Interface**:
   - Function: `main()`
     - Set up the page with an appropriate title and layout.
     - Use two columns for analysis settings and displaying results.
     - Allow file upload and set analysis parameters:
       - Sliders for setting relative weights for `TIPO`.
       - Multi-selection for operators, food types, and diets.
       - Date selection for analysis period.
       - Checkbox to remove outliers.
       - Button to start analysis.
     - After clicking "Generate":
       - Load and filter data.
       - Calculate the weighted average.
       - Generate and display histogram.
       - Show options to download PNG and CSV.
       - Include tables of statistics with/without outliers.

9. **Function Calls**:
   - Ensure the `main()` function is called using:
     ```python
     if __name__ == "__main__":
         main()
     ```

10. **General Requirements**:
    - Use consistent formatting and add docstrings to all functions.
    - Display warnings for incorrect/missing inputs.
    - Ensure timestamps are generated in Brasília time.

### Running the Application
To run the app:
```bash
streamlit run batidas.py
```

11. **General Requirements**:
    - Use consistent formatting and add docstrings to all functions explaining their purpose, input parameters, and outputs.
    - Make sure that all interactions (uploads, selections, and filters) are user-friendly, and that appropriate warnings are displayed if expected input is missing or incorrect.
    - Include handling for time zone settings to display generation timestamps in a specific format (e.g., Brasília time).

The program should ensure clear code organization, modularity, and proper documentation throughout. The objective is to create a web-based interactive data visualization tool using Streamlit that allows users to upload a dataset, set weights, filter data, analyze it, and visualize the results through histograms.

## Running the Application

To run the Streamlit app, use the following command:

```bash
streamlit run batidas.py
```

## GitHub Commands

```bash
git status
git add batidas.py instructions_for_app_batidas.md requirements.txt pseudocode.md
git commit -m "Updated version of batidas app - improvements in graph and statistics table"
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
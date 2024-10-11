Write a Python program using the Streamlit framework to create a data analysis web app for visualizing batch-level metrics using histograms. The program should meet the following requirements:

1. **Dependencies**:
   - Use `pandas`, `numpy`, `matplotlib`, and `streamlit`.
   - Import additional libraries such as `datetime`, `io`, `base64`, and `pytz` for specific functionalities.

2. **Load and Process Data**:
   - Create a function named `load_and_process_data(uploaded_file)`:
     - Load an Excel file (`.xlsx`) while skipping the first two rows, which may contain metadata.
     - Remove the first column of the dataset since it is considered irrelevant.
     - Ensure that the column 'DIFERENÇA (%)' is present, and convert its values to numeric.
     - Convert the column 'DATA' to datetime format to facilitate date-based filtering.
     - Return the processed DataFrame.

3. **Weighted Average Calculation**:
   - Create a function named `calculate_weighted_average(df)`:
     - Explicitly access the columns `PREVISTO (KG)`, `REALIZADO (KG)`, and `DIFERENÇA (%)` by their respective positions in the DataFrame.
     - Calculate the absolute value of the percentage difference for each row.
     - Group data by a column named 'COD. BATIDA' and calculate the weighted average of the differences:
       - Calculate the contribution of each ingredient by multiplying the planned quantity by the percentage difference.
       - Divide the sum of contributions by the total planned quantity for each batch to compute the weighted average.
     - Return a new DataFrame containing the weighted averages.

4. **Outlier Removal**:
   - Create a function named `remove_outliers_from_df(df, column)`:
     - Calculate the interquartile range (IQR) of the specified column.
     - Define an upper bound to identify extreme values as outliers.
     - Return a DataFrame excluding rows with values above the upper bound.

5. **Data Filtering**:
   - Create a function named `filter_data(df, operadores, alimentos, dietas, start_date, end_date)`:
     - Convert `start_date` and `end_date` to datetime.
     - Filter the DataFrame based on date range and the selection criteria for operators (`OPERADOR`), food types (`ALIMENTO`), and diets (`NOME`).
     - Return the filtered DataFrame.

6. **Histogram Creation**:
   - Create a function named `create_histogram(df, title, start_date, end_date, remove_outliers=False)`:
     - Use `matplotlib` to create a histogram based on the column 'MÉDIA PONDERADA (%)'.
     - Apply optional outlier removal if specified.
     - Color the bars using a gradient based on their value:
       - Values above a threshold (3%) should be colored with varying intensity of red.
       - Values below the threshold should be colored green.
     - Set appropriate labels, grid lines, and add a vertical dashed line at the 3% value.
     - Include text in the footer of the histogram detailing the analysis period, the total number of batches, and the generation timestamp.
     - Return the figure object.

7. **Image Saving and Download Link**:
   - Create a function named `save_histogram_as_image(fig)`:
     - Save the histogram figure as a PNG file and return an HTML link for downloading the image.

8. **Statistics Table Creation**:
   - Create a function named `save_statistics_as_csv(stats_df)`:
     - Save a DataFrame containing statistics to a CSV file and return an HTML link for downloading the file.

9. **Streamlit User Interface**:
   - Define a `main()` function:
     - Set up the Streamlit page configuration with an appropriate title and layout.
     - Use two columns: one for the analysis settings and one for displaying results.
     - Allow the user to upload an Excel file and set analysis parameters:
       - Multi-selection for operators, food types, and diets.
       - Date input for selecting the analysis period.
       - Checkbox to allow outlier removal.
       - Button to initiate the analysis.
     - Upon clicking the "Generate" button:
       - Load and filter the data based on user inputs.
       - If the filtered data is not empty:
         - Calculate the weighted average of percentage differences.
         - Generate a histogram using the weighted averages.
         - Display the histogram and offer the option to download it as a PNG.
         - Create and display a table of relevant statistics, with the option to download it as a CSV file.

10. **Function Calls**:
    - Ensure the `main()` function is called when the script runs, using:
      ```python
      if __name__ == "__main__":
          main()
      ```

11. **General Requirements**:
    - Use consistent formatting and add docstrings to all functions explaining their purpose, input parameters, and outputs.
    - Make sure that all interactions (uploads, selections, and filters) are user-friendly, and that appropriate warnings are displayed if expected input is missing or incorrect.
    - Include handling for time zone settings to display generation timestamps in a specific format (e.g., Brasília time).

The program should ensure clear code organization, modularity, and proper documentation throughout. The objective is to create a web-based interactive data visualization tool using Streamlit that allows users to upload a dataset, filter data, analyze it, and visualize the results through histograms.

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
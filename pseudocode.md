# Pseudocode for Data Analysis Application using Streamlit

## 1. **Import Dependencies**:
   - Import required libraries: Streamlit, Pandas, Numpy, Matplotlib, Datetime, IO, Base64, Pytz.

## 2. **Define Functions**:

   a. `load_and_process_data(uploaded_file)`:
   - Load Excel file (`.xlsx`), skipping the first 2 rows.
   - Remove the first column as it is irrelevant.
   - Ensure 'DIFERENÇA (%)' column is present and convert its values to numeric.
   - Convert 'DATA' column to datetime format for filtering.
   - Return the processed DataFrame.

   b. `calculate_weighted_average_with_weights(df, pesos_relativos)`:
   - Extract specific columns: 'PREVISTO (KG)', 'REALIZADO (KG)', and 'DIFERENÇA (%)'.
   - Calculate the absolute value of 'DIFERENÇA (%)' for each row.
   - Assign relative weights for each 'TIPO' of food based on user inputs (`pesos_relativos`).
   - Calculate the adjusted planned quantity (`PESO AJUSTADO`) by multiplying 'PREVISTO (KG)' by the relative weight (`PESO RELATIVO`).
   - Group data by 'COD. BATIDA'.
   - Calculate the contribution for each ingredient using `PESO AJUSTADO * DIFERENÇA (%)`.
   - Calculate the weighted average by dividing the sum of contributions by the total adjusted planned quantity for each batch.
   - Return a DataFrame containing the weighted averages for each batch.

   c. `remove_outliers_from_df(df, column)`:
   - Calculate the interquartile range (IQR) using Q1 and Q3.
   - Determine the upper bound for detecting outliers as `Q3 + 1.5 * IQR`.
   - Return a DataFrame excluding rows with values above the upper bound.

   d. `filter_data(df, operadores, alimentos, dietas, start_date, end_date)`:
   - Convert `start_date` and `end_date` to datetime format.
   - Filter the data based on the provided date range.
   - Apply additional filters for 'OPERADOR', 'ALIMENTO', and 'NOME' fields.
   - Return the filtered DataFrame.

   e. `create_histogram(df, title, start_date, end_date, remove_outliers=False)`:
   - Optionally remove outliers from the 'MÉDIA PONDERADA (%)' column using `remove_outliers_from_df()`.
   - Use Matplotlib to create a histogram from the 'MÉDIA PONDERADA (%)' column.
   - Apply a color scheme to histogram bars:
     - Color bars red for values greater than or equal to 3%, with varying intensity.
     - Color bars green for values below 3%, with intensity based on proximity to 0.
   - Set appropriate labels, add a vertical dashed line at 3% to indicate a threshold, and add grid lines.
   - Add footer information including the analysis period, the total number of batches, and the generation timestamp in Brasília time.
   - Return the figure object.

   f. `save_histogram_as_image(fig)`:
   - Save the histogram figure as a PNG file using a `BytesIO` buffer.
   - Generate an HTML link for downloading the image.
   - Return the download link.

   g. `save_statistics_as_csv(stats_df)`:
   - Save a DataFrame containing calculated statistics as a CSV file.
   - Generate an HTML link for downloading the CSV.
   - Return the download link.

## 3. **Main Function (`main()`)**:

   - Set up Streamlit page configuration with a title and layout.
   - Create two columns: one for analysis settings and one for displaying results.

   **Settings Column**:
   - Upload an Excel file.
   - Call `load_and_process_data()` to process the uploaded file.
   - If the data loads successfully:
     - Display sliders for setting relative weights for each type of food (`TIPO`).
     - Display selection options for filtering: operators (`OPERADOR`), food types (`ALIMENTO`), and diets (`NOME`).
     - Provide date inputs for selecting the analysis period (`start_date` and `end_date`).
     - Include a checkbox to allow outlier removal.
     - Display a button labeled "Generate" to initiate the analysis.

   **Results Column**:
   - If the "Generate" button is clicked:
     - Filter the data using `filter_data()` based on user selections.
     - If the filtered dataset is not empty:
       - Calculate weighted averages for percentage differences using `calculate_weighted_average_with_weights()`.
       - Create a histogram of the weighted averages using `create_histogram()`.
       - Display the histogram using Streamlit's `st.pyplot()` function.
       - Offer the option to download the histogram as a PNG file using `save_histogram_as_image()`.
       - Create and display a table of relevant statistics (both with and without outliers).
       - Provide an option to download the statistics as a CSV file using `save_statistics_as_csv()`.

## 4. **Entry Point**:
   - Ensure `main()` is called when the script runs:
   ```python
   if __name__ == "__main__":
       main()

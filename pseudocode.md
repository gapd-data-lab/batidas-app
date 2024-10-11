1. **Import Dependencies**:
   - Import required libraries: Streamlit, Pandas, Numpy, Matplotlib, Datetime, IO, Base64, Pytz.

2. **Define Functions**:

   a. `load_and_process_data(uploaded_file)`:
   - Load Excel file, skipping first 2 rows.
   - Remove first column.
   - Check for 'DIFERENÇA (%)' column, convert to numeric.
   - Convert 'DATA' column to datetime format.
   - Return processed DataFrame.

   b. `calculate_weighted_average(df)`:
   - Extract columns: 'PREVISTO (KG)', 'REALIZADO (KG)', 'DIFERENÇA (%)' from specific positions.
   - Calculate absolute difference percentage for each row.
   - Group data by 'COD. BATIDA'.
   - Calculate contribution for each ingredient: `planned_quantity * difference_percentage`.
   - Calculate weighted average: `sum(contributions) / total_planned_quantity`.
   - Return DataFrame with weighted averages.

   c. `remove_outliers_from_df(df, column)`:
   - Calculate IQR (Q1 and Q3).
   - Determine upper bound for outlier detection.
   - Return DataFrame without outlier rows.

   d. `filter_data(df, operadores, alimentos, dietas, start_date, end_date)`:
   - Convert `start_date` and `end_date` to datetime.
   - Filter data based on date range.
   - Apply filters for 'OPERADOR', 'ALIMENTO', 'NOME'.
   - Return filtered DataFrame.

   e. `create_histogram(df, title, start_date, end_date, remove_outliers=False)`:
   - Create histogram using Matplotlib.
   - Optionally remove outliers from 'MÉDIA PONDERADA (%)' column.
   - Color histogram bars based on thresholds (red for above, green for below).
   - Add labels, grid, and vertical line at 3%.
   - Add footer with analysis period and timestamp.
   - Return figure.

   f. `save_histogram_as_image(fig)`:
   - Save histogram as PNG.
   - Generate HTML link for download.
   - Return download link.

   g. `save_statistics_as_csv(stats_df)`:
   - Save DataFrame as CSV.
   - Generate HTML link for download.
   - Return download link.

3. **Main Function (`main()`)**:

   - Configure Streamlit page: title and layout.
   - Create two columns: one for analysis settings, one for results.
   - In settings column:
     - Upload Excel file.
     - Call `load_and_process_data()`.
     - If data loaded successfully:
       - Set filter options: operators, food types, diets.
       - Date range input.
       - Checkbox for outlier removal.
       - Button to initiate analysis.
   - In results column:
     - If analysis button is clicked:
       - Filter data with `filter_data()`.
       - If filtered data is not empty:
         - Calculate weighted averages with `calculate_weighted_average()`.
         - Create histogram with `create_histogram()`.
         - Display histogram using Streamlit.
         - Offer histogram download using `save_histogram_as_image()`.
         - Create and display statistics table.
         - Offer statistics download using `save_statistics_as_csv()`.

4. **Entry Point**:
   - Call `main()` when script is executed.

## Program Execution
CALL main() 
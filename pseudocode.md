FUNCTION main():
    INITIALIZE Streamlit page configuration
    
    CREATE two-column layout
    
    IN column1:
        DISPLAY "Analysis Configuration"
        REQUEST Excel file upload
        
        IF file_uploaded:
            data = LOAD_AND_PROCESS_DATA(file)
            
            IF data is not null:
                DISPLAY date range selector
                DISPLAY multi-select for foods
                DISPLAY multi-select for diets
                DISPLAY multi-select for operators
                DISPLAY checkbox for outlier removal
                DISPLAY "Generate" button
    
    IN column2:
        IF file_uploaded AND generate_button_clicked AND data is not null:
            DISPLAY "Analysis Results - Confinement"
            
            filtered_data = FILTER_DATA(data, operators, foods, diets, start_date, end_date)
            
            IF filtered_data is empty:
                DISPLAY warning "Insufficient data for analysis"
            ELSE:
                mean_difference_per_batida = CALCULATE mean difference per batida
                
                histogram = CREATE_HISTOGRAM(mean_difference_per_batida, title, start_date, end_date, remove_outliers)
                DISPLAY histogram
                
                OFFER histogram download as PNG
                
                statistics = CALCULATE_STATISTICS(mean_difference_per_batida)
                DISPLAY statistics table
                
                OFFER statistics download as CSV
                
                IF remove_outliers:
                    DISPLAY note about outlier removal

## Auxiliary Functions

FUNCTION LOAD_AND_PROCESS_DATA(file):
    LOAD Excel data skipping 2 rows
    REMOVE first column
    STANDARDIZE column names
    CONVERT 'DIFERENÇA (%)' column to numeric
    CONVERT 'DATA' column to datetime
    RETURN processed data

FUNCTION CALCULATE_STATISTICS(data, column):
    COMPUTE basic statistics (count, mean, median)
    CALCULATE quartiles and IQR
    DEFINE outlier boundaries
    COMPUTE statistics by difference range
    CALCULATE statistics without outliers
    RETURN statistics with and without outliers

FUNCTION FILTER_DATA(data, operators, foods, diets, start_date, end_date):
    FILTER data by date range
    IF operators doesn't include 'All' THEN FILTER by operators
    IF foods doesn't include 'All' THEN FILTER by foods
    IF diets doesn't include 'All' THEN FILTER by diets
    RETURN filtered data

FUNCTION CREATE_HISTOGRAM(data, title, start_date, end_date, remove_outliers):
    IF remove_outliers THEN REMOVE outliers from data
    CALCULATE X-axis limits
    CREATE histogram using matplotlib
    CUSTOMIZE bar colors
    ADD vertical line at zero
    CONFIGURE grid, ticks, and labels
    ADD footer information
    RETURN histogram figure

FUNCTION SAVE_HISTOGRAM_AS_IMAGE(figure):
    SAVE figure as PNG in memory buffer
    ENCODE image to base64
    CREATE HTML download link
    RETURN HTML link

FUNCTION SAVE_STATISTICS_AS_CSV(statistics):
    CONVERT statistics to CSV
    ENCODE CSV to base64
    CREATE HTML download link
    RETURN HTML link

## Program Execution
CALL main()